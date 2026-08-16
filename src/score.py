"""Pull the live feed, score the events with the optimal model, and store the results."""
import joblib
import pandas as pd
from sqlalchemy import create_engine
from src import config, extract, transform

def main():
    """Load the stored model and medians, then read the live feed, make predictions,
    and store those predictions back into SLQ."""
    # load the optimal model
    model = joblib.load(config.MODEL_PATH)

    # create connection to sql
    engine = create_engine(config.CONNECTION_STRING)

    # load medians and turn into a dictionary
    df_medians = pd.read_sql(f"SELECT * FROM {config.TBL_MEDIANS}", con=engine)
    medians = dict(zip(df_medians["feature"], df_medians["median"]))

    # load the live feed
    df = extract.get_live()

    # clean the live feed
    df = transform.clean_events(df, medians)

    # check if it's empty. do this after cleaning because cleaning drops
    # non-earthquake events
    if df.empty:
        print("No live events to score.")
        return

    # predict significant event
    probs = model.predict_proba(df[config.FEATURES])[:, 1]

    # pull out stored columns, add the prediction, and the timetamp
    df_output = df[["id", "time", "mag", "net"] + config.FEATURES].assign(
          probability=probs, scored_at=pd.Timestamp.now()
    )
    
    # write into the sql database
    df_output.to_sql(config.TBL_PREDICTIONS, con=engine, if_exists="append", index=False)

    # print how many events we scored
    print(f"Scored {len(df_output)} at {pd.Timestamp.now()}")

if __name__ == "__main__":
      main()



    

    