"""Transform: clean and transform data both training and live use."""
import pandas as pd
import dask.dataframe as dd
from src import config, extract

def clean_events(df, medians):
    """Filters to earthquakes, drops missing mag events, imputes median for other NA, creates
    new target variable."""
    # subset to just earthquake events
    df = df[df["type"] == "earthquake"]

    # drop rows that don't have magnitude
    df = df.dropna(subset=["mag"])

    # fill non-mag missing values
    # the longitude, latitude, and depth medians are useless but never used
    df = df.fillna(medians)

    # add the variable we're trying to predict and return
    return df.assign(**{config.TARGET: (df["mag"] >= config.MAG_THRESHOLD).astype(int)})

def transform_bulk():
    """Use Dask to bulk import and process downloaded CSVs."""

    # read the downloaded csvs
    ddf = dd.read_csv(str(config.LANDING_DIR / "*.csv"),
                      usecols=config.FEATURES + ["mag", "type", "net"],
                      dtype={"nst": "float64"}
    )

    # calcualte approximate medians
    medians = ddf[config.FEATURES].median_approximate().compute().to_dict()

    # run clean_events which filters, dorps missing mag, and imputes medians
    ddf = clean_events(ddf, medians)

    # run dask to get a df
    df = ddf.compute()

    # merge the dataframes together
    df = df.merge(extract.read_networks(), on="net", how="left")

    # return the merged and the medians
    return df, medians

