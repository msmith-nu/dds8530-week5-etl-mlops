"""Extract phase: bulk CSV download, live USGS API feed, SQLite lookup table."""
import pandas as pd
import requests
from sqlalchemy import create_engine
from src import config

# usgs limits how much we can download at once. so download in quarters. to
# download in quarters, have to calculate quarters

def get_quarters(start_date, end_date):
    """Returns quarter starts and ends from a start and end date."""

    # get equally spaced start and end dates
    dates = pd.date_range(start_date, end_date, freq="QS")

    # convert the timestamp to strings
    str_dates = [x.strftime("%Y-%m-%d") for x in dates]

    return list(zip(str_dates[:-1], str_dates[1:]))


def request_data(start_date, end_date, destination):
    """Pulls data from USGS API and saves it to disk."""

    # format api request
    r = requests.get(config.URL_HISTORY, params={"format" : "csv", 
                                                   "starttime" : start_date,
                                                   "endtime" : end_date,
                                                   "minmagnitude" : config.MAG_MIN
                                                   }
    )

    # check api status
    r.raise_for_status()

    # write results to disk
    destination.write_text(r.text)

    return destination


def get_data(dates):
    """From a list of start and end dates, submits requests if file
    doesn't already exist."""

    for date in dates:
        start = date[0]
        end = date[1]

        # configure file path and name
        current = config.LANDING_DIR / f"{start}.csv"

        # check if this one was already downloaded, if so skip
        if current.exists():
            # print a status update
            print(f"Data file for {start} already exists. Skipping.")
            continue

        # if it doesn't already exist, pull and write it
        request_data(start_date=start, end_date=end, destination=current)

        # print a status update
        print(f"Pulled data file for {start}.")


        
def get_live():
    """Pulls json out of live feed and processes it to be added to DataFrame."""
    # store url      
    r = requests.get(config.URL_LIVE)
    # check api status
    r.raise_for_status()

    # extract json data
    live = r.json()

    # start an empty list
    events = []

    # iterature through the features in live request return
    for feature in live["features"]:
        coordinates = feature["geometry"]["coordinates"]
        properties = feature["properties"]
        events.append(
            {
                "time" : properties.get("time"),
                "latitude" : coordinates[1],
                "longitude" : coordinates[0],
                "depth" : coordinates[2],
                "mag" : properties.get("mag"),
                "nst" : properties.get("nst"),
                "gap" : properties.get("gap"),
                "dmin" : properties.get("dmin"),
                "rms" : properties.get("rms"),
                "net" :properties.get("net"),
                "id" : feature["id"]
            }
        )

    # return a DataFrame
    return pd.DataFrame(events)

# we're only going to use the alaska network because data changes between networks. so stor elookup table
def seed_networks():
    """Stores the network lookup table in SQL."""

    network_codes = {
        "net": [
            "ak", "ci", "nc", "hv", "us", "nn", "uu", "uw", "tx", "pr"
        ],
        "network": [
            "Alaska Earthquake Center",
            "California Integrated Seismic Network",
            "Northern California Seismic System",
            "Hawaiian Volcano Observatory",
            "USGS National Earthquake Information Center",
            "Nevada Seismological Laboratory",
            "University of Utah Seismograph Stations",
            "Pacific Northwest Seismic Network",
            "Texas Seismological Network",
            "Puerto Rico Seismic Network",
        ]
    }

    # convert to DataFrame
    df_network_codes = pd.DataFrame(network_codes)

    # create SQLAclhemy engine
    engine = create_engine(config.CONNECTION_STRING)

    # create table in database
    df_network_codes.to_sql(config.TBL_NETWORKS, con=engine, if_exists="replace", index=False)

# now code how to lookup networks
def read_networks():
    """Reads the network table pack into a DataFrame."""
    engine = create_engine(config.CONNECTION_STRING)
    return pd.read_sql(config.TBL_NETWORKS, con=engine)

# now main() which will be what runs
def main():
    """Runs seed_networks, get_quarters, and get_data."""
    # create database and networks table
    seed_networks()

    # build timeframe window query
    dates = get_quarters(config.START_DATE, config.END_DATE)

    # pull down data from time frame
    get_data(dates)

    # print summary line
    print(f"Finished pulling from {config.START_DATE} to {config.END_DATE}.")


if __name__ == "__main__":
    main()

