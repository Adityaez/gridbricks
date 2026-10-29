"""Unit tests for cutoff selection and accuracy calculations."""
import pytest
import pandas as pd
from app.services.analytics import compute_metrics


def test_metrics_empty_dataframe():
    """Verify metrics calculation returns safe None values on empty input."""
    result = compute_metrics(pd.DataFrame())
    assert result["mae_mw"] is None
    assert result["rmse_mw"] is None
    assert result["wape_percent"] is None
    assert result["matched_intervals"] == 0

