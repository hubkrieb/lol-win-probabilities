import argparse
from src.models.utils import load_data, init_model

def predict(model, X, proba = True):
    if proba == True:
        y_pred = model.predict_proba(X)
    else:
        y_pred = model.predict(X)
    return y_pred

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', type = str, help = 'path of the data')
    parser.add_argument('--model_path', type = str, help = 'path to the model')

    args = parser.parse_args()
    data_path, model_path = args.data_path, args.model_path

    X, y = load_data(data_path, test_size = 0)
    model = init_model(model_path)
    results = predict(model, X)

    import pandas as pd

    dataset = pd.read_csv('data/competitive_dataset.csv', index_col = None)

    preds_df = pd.DataFrame()
    preds_df['Id'] = dataset['match_id'] + '_' + X['minute'].astype(str)
    preds_df['RiotPlatformGameId'] = dataset['match_id']
    preds_df['Minute'] = X['minute']
    preds_df['GoldDiff'] = dataset[[f'player{i}_gold' for i in range(1, 6)]].sum(axis = 1) - dataset[[f'player{i}_gold' for i in range(6, 11)]].sum(axis = 1)
    preds_df['WinProbability'] = results[:, 0]

    preds_df.to_csv('data/competitive_predictions.csv', index = None)