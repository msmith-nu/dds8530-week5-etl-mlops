"""Runs extract, then transforms them, then loads them into SQL."""
import pandas as pd
from sqlalchemy import create_engine
from src import config, extract, transform, logs

# set up logging
log = logs.get_logger(__name__)

def load_events(df):
    """Writes a cleaned DataFrame into the SQL database."""
    engine = create_engine(config.CONNECTION_STRING)

    # write the cleaned up df into the sql table
    df.to_sql(config.TBL_CLEAN, con=engine, if_exists="replace", index=False, chunksize=10_000)


def load_medians(medians):
    """Converts medians dict into a DataFrame then stores it in SQL."""

    engine = create_engine(config.CONNECTION_STRING)

    df = pd.DataFrame({"feature": list(medians.keys()),
                  "median": list(medians.values())})

    df.to_sql(config.TBL_MEDIANS, con=engine, if_exists="replace", index=False)

def main():
    """Runs extract, then transform_bulk, then loads events and medians and prints
    how many rows it got."""
    extract.main()

    df, medians = transform.transform_bulk()

    load_events(df)

    load_medians(medians)

    log.info(f"Wrote {len(df)} rows to {config.TBL_CLEAN}.")

if __name__ == "__main__":
    main()