"""Set up project wide paths, URLs, and constants."""

from pathlib import Path

# file paths

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
LANDING_DIR = DATA_DIR / "raw"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
LOG_DIR = BASE_DIR / "logs"
CATALOG_DB = WAREHOUSE_DIR / "quakes.db"
MODEL_PATH = WAREHOUSE_DIR / "model.pkl"
LOG_FILE = LOG_DIR / "pipeline.log"

# data urls

URL_HISTORY = "https://earthquake.usgs.gov/fdsnws/event/1/query"
URL_LIVE = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"

# db info for SQLAlchemy

CONNECTION_STRING = f"sqlite:///{CATALOG_DB}"

# parameters

START_DATE = "2015-01-01"
END_DATE = "2026-01-01"
MAG_MIN = 2.5

# tables

TBL_CLEAN = "events_clean"
TBL_NETWORKS = "networks"
TBL_PREDICTIONS = "predictions"
TBL_MEDIANS = "medians"

# constants

MAG_THRESHOLD = 4.0
TARGET = "is_significant"
FEATURES = ["depth", "latitude", "longitude", "nst", "gap", "dmin", "rms"]
TRAIN_NETWORK = "ak"
TEST_PORTION = 0.2
SEED = 2015
MLFLOW_EXPERIMENT = "Major_Earthquake_Classifier"

# mkdir

for directory in (LANDING_DIR, WAREHOUSE_DIR, LOG_DIR):
    directory.mkdir(parents=True, exist_ok=True)