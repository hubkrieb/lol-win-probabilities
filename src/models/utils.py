import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split

def load_data(file, test_size = 0.2, random_state = 2):
    if file.split('.')[-1] == 'gzip':
        features = pd.read_parquet(file)
    elif file.split('.')[-1] == 'csv':
        features = pd.read_csv(file, index_col = None)
    y = features.iloc[:, 1]
    X = features.iloc[:, 2:]
    y = y - 1
    if test_size > 0 and test_size < 1:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = test_size, random_state = random_state)
        return X_train, X_test, y_train, y_test
    else:
        return X, y

def init_model(file = None):
    model = xgb.XGBClassifier(
        n_estimators = 1000,
        max_depth = 9,
        min_child_weight = 1,
        gamma = 0.5,
        scale_pos_weight = 1,
        subsample = 0.85,
        colsample_bytree = 0.95,
        reg_lambda = 0.1,
        reg_alpha = 0.1,
        learning_rate = 0.5,
        objective = 'binary:logistic',
        eval_metric = ['rmse', 'error', 'logloss'],
        early_stopping_rounds = 10
        )
    if file is not None:
        model.load_model(file)
    return model