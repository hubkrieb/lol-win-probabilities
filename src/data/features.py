import argparse
import pandas as pd

def get_features(dataset):

    dataset_copy = dataset.copy()

    dataset_gold = dataset_copy[dataset_copy.columns[dataset_copy.columns.str.endswith('gold')]]
    dataset_copy[dataset_copy.columns[dataset_copy.columns.str.endswith('gold')]] = dataset_gold.div(dataset_gold.sum(axis = 1), axis = 0)

    dataset_xp = dataset_copy[dataset_copy.columns[dataset_copy.columns.str.endswith('xp')]]
    dataset_copy[dataset_copy.columns[dataset_copy.columns.str.endswith('xp')]] = dataset_xp.div(dataset_xp.sum(axis = 1), axis = 0).fillna(0)

    dataset_copy[dataset_copy.columns[dataset_copy.columns.str.endswith('Inhibitor')]] = (dataset_copy[dataset_copy.columns[dataset_copy.columns.str.endswith('Inhibitor')]].sub(dataset_copy['timestamp'], axis = 0)).clip(lower = 0)

    dataset_copy[dataset_copy.columns[dataset_copy.columns.str.startswith('team') & dataset_copy.columns.str.endswith('nashor')]] = (dataset_copy[dataset_copy.columns[dataset_copy.columns.str.startswith('team') & dataset_copy.columns.str.endswith('nashor')]].sub(dataset_copy['timestamp'], axis = 0)).clip(lower = 0)

    dataset_copy[dataset_copy.columns[dataset_copy.columns.str.startswith('team') & dataset_copy.columns.str.endswith('elderDragon')]] = (dataset_copy[dataset_copy.columns[dataset_copy.columns.str.startswith('team') & dataset_copy.columns.str.endswith('elderDragon')]].sub(dataset_copy['timestamp'], axis = 0)).clip(lower = 0)

    dataset_copy['team1_num_player_nashor'] = dataset_copy[dataset_copy.columns[(dataset_copy.columns.str.startswith('player1') | dataset_copy.columns.str.startswith('player2') | dataset_copy.columns.str.startswith('player3') | dataset_copy.columns.str.startswith('player4') | dataset_copy.columns.str.startswith('player5')) & dataset_copy.columns.str.endswith('nashor')]].gt(dataset_copy['timestamp'], axis = 0).sum(axis = 1)
    dataset_copy['team2_num_player_nashor'] = dataset_copy[dataset_copy.columns[(dataset_copy.columns.str.startswith('player6') | dataset_copy.columns.str.startswith('player7') | dataset_copy.columns.str.startswith('player8') | dataset_copy.columns.str.startswith('player9') | dataset_copy.columns.str.startswith('player10')) & dataset_copy.columns.str.endswith('nashor')]].gt(dataset_copy['timestamp'], axis = 0).sum(axis = 1)

    dataset_copy['team1_num_player_elder'] = dataset_copy[dataset_copy.columns[(dataset_copy.columns.str.startswith('player1') | dataset_copy.columns.str.startswith('player2') | dataset_copy.columns.str.startswith('player3') | dataset_copy.columns.str.startswith('player4') | dataset_copy.columns.str.startswith('player5')) & dataset_copy.columns.str.endswith('elderDragon')]].gt(dataset_copy['timestamp'], axis = 0).sum(axis = 1)
    dataset_copy['team2_num_player_elder'] = dataset_copy[dataset_copy.columns[(dataset_copy.columns.str.startswith('player6') | dataset_copy.columns.str.startswith('player7') | dataset_copy.columns.str.startswith('player8') | dataset_copy.columns.str.startswith('player9') | dataset_copy.columns.str.startswith('player10')) & dataset_copy.columns.str.endswith('elderDragon')]].gt(dataset_copy['timestamp'], axis = 0).sum(axis = 1)

    dataset_copy['minute'] = (dataset_copy['timestamp'] / 60000).round().astype(int)

    features = dataset_copy[dataset_copy.columns[~(dataset_copy.columns.str.endswith('champion') | dataset_copy.columns.str.endswith('respawn') | (dataset_copy.columns.str.startswith('player') & dataset_copy.columns.str.endswith('elderDragon')) | (dataset_copy.columns.str.startswith('player') & dataset_copy.columns.str.endswith('nashor')))]]
    features = features.drop(columns = ['timestamp'])
    features = features.round(3)
    return features

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_path', type = str, help = 'path of the dataset')
    parser.add_argument('--feature_path', type = str, help = 'path to save the resulting features')

    args = parser.parse_args()
    dataset_path, feature_path = args.dataset_path, args.feature_path

    dataset_extension = dataset_path.split('.')[-1]
    feature_extension = feature_path.split('.')[-1]

    if dataset_extension == 'csv':
        dataset = pd.read_csv(dataset_path, index_col = None)
    elif dataset_extension == 'gzip':
        dataset = pd.read_parquet(dataset_path)

    features = get_features(dataset)

    if feature_extension == 'csv':
        features.to_csv(feature_path, index = None)
    elif feature_extension == 'gzip':
        features.to_parquet(feature_path)