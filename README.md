# DDS8530 Week5 ETL-MLOPS Assignment
![CI](https://github.com/msmith-nu/dds8530-week5-etl-mlops/actions/workflows/ci.yml/badge.svg)

## Project Information

This repository is the code component of an assignment in DDS8530 where we were tasked with generating a pipeline which performed:

- Extracting data from an external database via API, transform it, then load it into a local SQL database
- Use said data in a machine learning algorithm that predicts classification of earthquakes as being significant (magnitude >= 4.0) or not based on their metadata. The optimized machine learning algorithm (logistic regression) achieves an AUC of 0.7732 with average precision of 0.1621 on 21,459 Alaska events.
- Configure that machine learning algorithm to be available via API to run on new data as part of a MLOps workflow.

## Stack

| Tool | Role in this project |
|---|---|
| `requests` | Pulls both USGS sources: quarterly bulk CSV batches and the live GeoJSON feed |
| `pandas` | DataFrame operations throughout; handles the small live batch at scoring time |
| `Dask` | Processes the full 313,181-row catalog across 44 partitions without loading it all into memory |
| `SQLAlchemy` | Reads the `networks` lookup table and writes every table to the warehouse |
| SQLite | The warehouse itself (`data/warehouse/quakes.db`) |
| `scikit-learn` | `Pipeline` with `StandardScaler` for normalization, `GridSearchCV` for tuning, logistic regression and random forest as candidates |
| `MLflow` | Experiment tracking: parameters, metrics, and model artifacts for every run |
| `joblib` | Serializes the winning pipeline to `model.pkl` |
| `FastAPI` | REST API exposing `/health`, `/predict`, and `/metrics` |
| `uvicorn` | ASGI server that runs the API |
| `prometheus-fastapi-instrumentator` | Exposes 14 Prometheus metric families, including per-endpoint request counts and latency histograms |
| Apache Airflow | Two DAGs: weekly ETL and retraining, hourly live scoring |
| `pytest` | Unit tests over the shared cleaning function |
| GitHub Actions | CI on every push: clean install, import check, test run |
| `logging` | Writes to console and `logs/pipeline.log` with timestamps and module names |

## Data Source

Data is pulled from a public United States Geological Survey API that is keyless with no rate limits. Both bulk historical CSV data is retrieved for training and then live GeoJSON data is retained for scoring.

## Setup

This project used a Python 3.12 virtual environment created with `uv`. It can be cloned and set up locally using the `requirements.txt` file.

## Pipeline workflow

1. `config.py` sets environmental constants
2. `extract.py` retrieves and extracts the data from the USGS sources (bulk historical is 2015-01-01 through 2026-01-01, chunked by quarters, for a total of 44 files, 56MB).
3. `transform.py` cleans and transforms the extracted data. Because results are distributed across multiple files this step uses **Dask** to process rows across 44 partitions and **pandas** for the live data processing. Cleaning function is written once and applied across all modules.
4. `load.py` loads the cleaned and transformed data into a SQL database using **SQLAlchemy** to write into a **SQLite** database in batches of 10,000 rows.
5. `train.py` scales the data with **scikit-learn** `StandardScaler` and optimizes a logistic regression and random forest classifier on the training dataset (using `GridSearchCV` for tuning) to predict whether the earthquake was significant (magnitude >= 4.0) based on metadata. The results are all logged to **MLflow**. One important point to note is that to avoid cross-network bleed over driving the training algorithm, only data from the Alaska network is used in training.
6. `score.py` uses the optimized and best performing model from `train.py` to calculate probabilities for new events retrieved from the USGS live feed.
7. `api/main.py` sets up an API allowing for the model to be accessed via URL to classify new input data.
8. `dags/` schedules weekly training data retrievals as well as hourly live data retrievals using Apache Airflow.
9. `tests/` contains 3 tests covering 5 behaviors to ensure proper continuous integration (CI) performance.
10. `logs.py` sets up a logging apparatus.

## How to Run

```bash
python -m src.load # ETL
python -m src.train # train and log to MLflow, save model
python -m src.score # pull live feed, score, and append predictions to SQL database
```

## Outputs

- `data/raw`: 44 quarterly CSVs
- `data/warehouse/quakes.db': 35MB SQLite with `events_clean` (310,330 rows), `networks` (10 area networks), `medians` (median values for missing data imputation in input features), `predictions` (appended per run).
- `data/warehouse/model.pkl`: the fitted pipeline including the fitted scaler
- `mlflow.db`: experiment tracking
- `logs/pipeline.log`: logging file

## API

- `uvicorn api.main:app`
- has functionality for `/health`, `/predict`, and `/metrics` requests (the latter using **Prometheus**).

**Example request:**

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "depth": 12.4,
    "latitude": 61.32,
    "longitude": -149.87,
    "nst": 42.0,
    "gap": 78.0,
    "dmin": 0.42,
    "rms": 0.51
  }'
```

**Example response:**

```
{
  "probability": 0.00021725060368453196,
  "is_significant": false
}
```

Probability is the estimate probability that the quake's magnitude was 4.0 or greater. The threshold for `is_significant` is 0.5.

## Airflow

Airflow requires four environment variables:

```bash
export AIRFLOW_HOME="$PWD/airflow_home" # state directory
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/dags" # where the configure DAGs live
export AIRFLOW__CORE__LOAD_EXAMPLES=False # turn off bundled DAGs
export PYTHONPATH="$PWD" # put repo on path
```

For first time setup:

```bash
airflow db migrate
airflow dags reserialize
```

**Note that** `airflow dags list` does not read the DAG folder so if run before `reserialize` it will report `No data found.`

To run the DAGs:
```bash
airflow dags test quake_etl_train # performs the data ETL and model training, scheduled weekly.
airflow dags test quake_score_live # retrieves live data and scores it, scheduled hoursly..
```


## Tests and CI

Several preconfigured tests are included:

`python -m pytest tests/ -v`

Cover filtering non-earthquake events, events missing a magnitude, events missing a non-magnitude value (for which the median should be imputed), events that are not significant, and events that are.

`.github/workflows/ci.yml` is configured to verify module imports and run test suite on a clean machine with every push using Github actions.
