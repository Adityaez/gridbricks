"""Elexon BMRS API client service for FUELHH and WINDFOR streams."""
import logging
from datetime import date
from typing import Optional
import httpx
import pandas as pd
from app.config import settings

logger = logging.getLogger(__name__)


class ElexonClient:
    """Client for querying Elexon BMRS data streams."""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url or settings.ELEXON_API_BASE_URL
        self.api_key = api_key or settings.ELEXON_API_KEY
        self.timeout = httpx.Timeout(20.0, connect=10.0)

    async def fetch_actual_wind(self, target_date: date) -> pd.DataFrame:
        """
        Fetch realized actual generation from FUELHH filtered to fuelType == 'WIND'.
        Returns normalized DataFrame with columns: ['startTime', 'generation', 'fuelType']
        """
        # Skeleton implementation for Phase 0
        return pd.DataFrame(columns=["startTime", "generation", "fuelType"])

    async def fetch_wind_forecasts(self, target_date: date) -> pd.DataFrame:
        """
        Fetch wind forecasts from WINDFOR.
        Returns normalized DataFrame with columns: ['startTime', 'publishTime', 'generation']
        """
        # Skeleton implementation for Phase 0
        return pd.DataFrame(columns=["startTime", "publishTime", "generation"])
