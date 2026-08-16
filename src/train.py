"""Train a classifier on warehouse data, tune it, and log everything to MLflow."""
import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, average_precision_score
from sqlalchemy import create_engine
import mlflow
import mlflow.sklearn
import joblib
from src import config


def load_training_data():
    """Connect to SQL, filter to training network and then run and return train test split using stratification."""
    # create engine to sql
    engine = create_engine(config.CONNECTION_STRING)

    df = pd.read_sql(f"SELECT * FROM {config.TBL_CLEAN} WHERE net = '{config.TRAIN_NETWORK}'", con=engine)

    X = df[config.FEATURES]
    y = df[config.TARGET]

    return train_test_split(
        X, y, test_size=config.TEST_PORTION, random_state=config.SEED, stratify=y
    )

# define the two models we're going to use
CANDIDATES = {
    "logreg": (LogisticRegression(max_iter=1000), {"logisticregression__C": [0.1, 1.0]}),
    "forest": (RandomForestClassifier(n_jobs=-1, random_state=config.SEED), {"randomforestclassifier__n_estimators": [100,300]})
}

def train_models(X_train, X_test, y_train, y_test):
    """Use sklearn grid search CV and MLFlow to test logistic regression and random forest classifier
    to find best model on training data by testing on testing data."""

    # set experiment
    mlflow.set_experiment(config.MLFLOW_EXPERIMENT)

    # set tracking variables
    score_best = 0
    model_best = None

    # iterate through each candidate
    for candidate, (estimator, grid) in CANDIDATES.items():
        with mlflow.start_run(run_name=candidate):
            pipeline = make_pipeline(StandardScaler(), estimator)
            result = GridSearchCV(pipeline, grid, scoring="roc_auc", cv=3, n_jobs=-1).fit(X_train, y_train)
            probs = result.predict_proba(X_test)[:, 1]
            auc = roc_auc_score(y_test, probs)
            prec = average_precision_score(y_test, probs)
            # log results with MLFlow
            mlflow.log_params(result.best_params_)
            mlflow.log_metrics({
                "cv_auc": result.best_score_,
                "test_auc": auc,
                "test_prec": prec
            })
            mlflow.sklearn.log_model(result.best_estimator_, name=candidate)
            # print results
            print(f"Model: {candidate}. AUC: {auc}. Average Precision: {prec}")
            # store results if they're the best
            if auc > score_best:
                score_best = auc
                model_best = result.best_estimator_

    # print the final results
    print(f"Best Model: {model_best.steps[-1][0]} with score {score_best}.")

    # return the best results
    return model_best, score_best

def main():
    """Load the training and test datasets then run model training and save the results to disk."""
    X_train, X_test, y_train, y_test = load_training_data()

    model, score = train_models(X_train, X_test, y_train, y_test)

    joblib.dump(model, config.MODEL_PATH)

    print(f"Model {model.steps[-1][0]} saved to {config.MODEL_PATH}. Best score: {score}")

if __name__ == "__main__":
    main()