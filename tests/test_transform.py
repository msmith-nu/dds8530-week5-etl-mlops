"""Unit tests for the shared transform function. These are what CI runs."""
import pandas as pd
from src import config
from src.transform import clean_events

def sample_events():
    """Create events with known issues to confirm function working."""  
    return pd.DataFrame({
        "type": ["earthquake", "earthquake", "quarry blast", "earthquake", "earthquake"],
        "mag": [4.5, 2.0, 5.0, None, 3.0],
        "nst":       [10.0, 10.0, 10.0, 10.0, None],
        "depth":     [1.0, 1.0, 1.0, 1.0, 1.0],
        "latitude":  [1.0, 1.0, 1.0, 1.0, 1.0],
        "longitude": [1.0, 1.0, 1.0, 1.0, 1.0],
        "gap":       [1.0, 1.0, 1.0, 1.0, 1.0],
        "dmin":      [1.0, 1.0, 1.0, 1.0, 1.0],
        "rms":       [1.0, 1.0, 1.0, 1.0, 1.0],
    })

def test_noneq_missingmag_removed():
    df = clean_events(sample_events(), {"nst": 99.0})

    # should remove the non-earthquake and the missing mag
    assert len(df) == 3

def test_imputedmedian():
    df = clean_events(sample_events(), {"nst": 99.0})

    # it should have imputed the median of 99.0
    assert df["nst"][4] == 99.0

def test_significant():
    df = clean_events(sample_events(), {"nst": 99.0})

    # target should be 1 for the 1st and 0 for the 2nd
    assert df[config.TARGET][0] == 1 
    assert df[config.TARGET][1] == 0