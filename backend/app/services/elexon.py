"""Elexon BMRS API client service for FUELHH and WINDFOR streams with resilient ingestion and normalization."""
import asyncio
import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
import httpx
import pandas as pd
from app.config import settings

logger = logging.getLogger(__name__)


class ElexonClient:
    """
    Asynchronous client for querying Elexon BMRS datasets with automatic retries,
    in-memory caching, timestamp normalization, and validation.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = 20.0,
        max_retries: int = 3
    ):
        self.base_url = (base_url or settings.ELEXON_API_BASE_URL).rstrip("/")
        self.api_key = api_key or settings.ELEXON_API_KEY
        self.timeout = httpx.Timeout(timeout_seconds, connect=10.0)
        self.max_retries = max_retries
        self._cache: Dict[Tuple[str, str, str], pd.DataFrame] = {}

    def clear_cache(self) -> None:
        """Clear all in-memory cached responses."""
        self._cache.clear()

    async def _execute_request_with_retry(
        self,
        endpoint_path: str,
        params: Dict[str, Any]
    ) -> list:
        """
        Execute an HTTP GET request against Elexon BMRS with bounded exponential backoff.
        Retries on HTTP 429 (rate-limited) and 5xx server errors.
        """
        url = f"{self.base_url}/{endpoint_path.lstrip('/')}"
        headers = {
            "Accept": "application/json",
            "User-Agent": "WindSight-Backend/1.0"
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key

        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                    response = await client.get(url, params=params, headers=headers)
                    if response.status_code == 200:
                        return response.json()

                    if response.status_code in (429, 500, 502, 503, 504):
                        logger.warning(
                            f"Elexon API returned status {response.status_code} for {url} on attempt {attempt}/{self.max_retries}"
                        )
                        if attempt < self.max_retries:
                            backoff = 0.5 * (2 ** (attempt - 1))
                            await asyncio.sleep(backoff)
                            continue
                    response.raise_for_status()
            except (httpx.RequestError, httpx.HTTPStatusError) as exc:
                last_exception = exc
                logger.warning(f"Request error on attempt {attempt}/{self.max_retries}: {exc}")
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2 ** (attempt - 1)))
                else:
                    break

        raise RuntimeError(
            f"Failed to fetch data from Elexon endpoint '{endpoint_path}' after {self.max_retries} attempts: {last_exception}"
        )

    async def fetch_actual_wind(self, start_date: date, end_date: date) -> pd.DataFrame:
        """
        Fetch realized generation from FUELHH, filter strictly to fuelType == 'WIND',
        and normalize timestamps to UTC.

        Returns DataFrame columns:
            - startTime: datetime64[ns, UTC]
            - publishTime: datetime64[ns, UTC]
            - settlementDate: str (YYYY-MM-DD)
            - settlementPeriod: int (1-48)
            - fuelType: str ('WIND')
            - actual_mw: float
        """
        cache_key = ("FUELHH_WIND", str(start_date), str(end_date))
        if cache_key in self._cache:
            logger.info(f"Returning cached FUELHH data for {start_date} to {end_date}")
            return self._cache[cache_key].copy()

        params = {
            "settlementDateFrom": str(start_date),
            "settlementDateTo": str(end_date)
        }
        raw_data = await self._execute_request_with_retry("datasets/FUELHH/stream", params)
        normalized_df = self.normalize_fuelhh(raw_data)
        self._cache[cache_key] = normalized_df
        return normalized_df.copy()

    def normalize_fuelhh(self, records: list) -> pd.DataFrame:
        """
        Pure data normalization function for FUELHH records.
        Separated for deterministic offline unit testing.
        """
        if not records:
            return pd.DataFrame(
                columns=["startTime", "publishTime", "settlementDate", "settlementPeriod", "fuelType", "actual_mw"]
            )

        df = pd.DataFrame(records)

        # Ensure required columns exist
        required_cols = {"startTime", "generation", "fuelType"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"FUELHH records missing required fields: {missing}")

        # 1. Filter strictly for fuelType == 'WIND'
        df = df[df["fuelType"].astype(str).str.strip().str.upper() == "WIND"].copy()
        if df.empty:
            return pd.DataFrame(
                columns=["startTime", "publishTime", "settlementDate", "settlementPeriod", "fuelType", "actual_mw"]
            )

        # 2. Normalize timestamps to UTC
        df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
        if "publishTime" in df.columns:
            df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)
        else:
            df["publishTime"] = df["startTime"]

        # 3. Validate generation values (numeric and non-negative)
        df["actual_mw"] = pd.to_numeric(df["generation"], errors="coerce")
        # Reject nulls or negative values
        df = df[df["actual_mw"].notna() & (df["actual_mw"] >= 0)].copy()

        # 4. Standardize settlementPeriod and settlementDate
        if "settlementPeriod" in df.columns:
            df["settlementPeriod"] = pd.to_numeric(df["settlementPeriod"], errors="coerce").fillna(0).astype(int)
        else:
            df["settlementPeriod"] = 0

        if "settlementDate" not in df.columns or df["settlementDate"].isna().all():
            df["settlementDate"] = df["startTime"].dt.strftime("%Y-%m-%d")

        # 5. Deterministic deduplication policy:
        # Keep latest record if duplicate startTime exists
        df = df.sort_values(by=["startTime", "publishTime"]).drop_duplicates(subset=["startTime"], keep="last")

        df = df.sort_values(by="startTime").reset_index(drop=True)
        return df[["startTime", "publishTime", "settlementDate", "settlementPeriod", "fuelType", "actual_mw"]]

    async def fetch_wind_forecasts(self, start_date: date, end_date: date) -> pd.DataFrame:
        """
        Fetch WINDFOR wind forecasts that cover delivery intervals in [start_date, end_date].
        Queries publications from (start_date - 2 days) to (end_date + 1 day) to capture
        both day-ahead decision cutoff publications and real-time revisions.

        Returns DataFrame columns:
            - startTime: datetime64[ns, UTC]
            - publishTime: datetime64[ns, UTC]
            - forecast_mw: float
        """
        cache_key = ("WINDFOR", str(start_date), str(end_date))
        if cache_key in self._cache:
            logger.info(f"Returning cached WINDFOR data for {start_date} to {end_date}")
            return self._cache[cache_key].copy()

        # Query publications starting 2 days prior to ensure day-ahead forecasts are retrieved
        pub_from = datetime.combine(start_date - timedelta(days=2), time.min, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        pub_to = datetime.combine(end_date, time.max, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {
            "publishDateTimeFrom": pub_from,
            "publishDateTimeTo": pub_to
        }
        raw_data = await self._execute_request_with_retry("datasets/WINDFOR/stream", params)
        normalized_df = self.normalize_windfor(raw_data, start_date, end_date)
        self._cache[cache_key] = normalized_df
        return normalized_df.copy()

    def normalize_windfor(self, records: list, start_date: Optional[date] = None, end_date: Optional[date] = None) -> pd.DataFrame:
        """
        Pure data normalization function for WINDFOR records.
        Filters to target delivery interval window and normalizes timestamps.
        """
        if not records:
            return pd.DataFrame(columns=["startTime", "publishTime", "forecast_mw"])

        df = pd.DataFrame(records)

        required_cols = {"startTime", "publishTime", "generation"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"WINDFOR records missing required fields: {missing}")

        # 1. Normalize timestamps to UTC
        df["startTime"] = pd.to_datetime(df["startTime"], utc=True)
        df["publishTime"] = pd.to_datetime(df["publishTime"], utc=True)

        # 2. Filter to target delivery range if provided
        if start_date is not None:
            min_delivery = pd.Timestamp(datetime.combine(start_date, time.min, tzinfo=timezone.utc))
            df = df[df["startTime"] >= min_delivery]
        if end_date is not None:
            # End of delivery period: end_date 23:59:59
            max_delivery = pd.Timestamp(datetime.combine(end_date, time.max, tzinfo=timezone.utc))
            df = df[df["startTime"] <= max_delivery]

        if df.empty:
            return pd.DataFrame(columns=["startTime", "publishTime", "forecast_mw"])

        # 3. Validate generation values (numeric and non-negative)
        df["forecast_mw"] = pd.to_numeric(df["generation"], errors="coerce")
        df = df[df["forecast_mw"].notna() & (df["forecast_mw"] >= 0)].copy()

        # 4. Deterministic deduplication policy:
        # If identical (startTime, publishTime) appears multiple times, retain last
        df = df.drop_duplicates(subset=["startTime", "publishTime"], keep="last")

        df = df.sort_values(by=["startTime", "publishTime"]).reset_index(drop=True)
        return df[["startTime", "publishTime", "forecast_mw"]]
