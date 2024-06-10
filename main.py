from sqlalchemy import create_engine
import os
import pandas as pd
from src.data.utils import get_games
from src.data.dataset import get_competitive_match_data
from src.data.features import get_features
from src.models.inference import predict
from src.models.utils import init_model

def main():
    """ Update the database with new games data """

    engine = create_engine(os.environ.get('DATABASE_URL'))

    oldest_date = pd.to_datetime(pd.read_sql_query('SELECT MAX("DateTime_UTC") AS latest_date FROM competitive_games', con = engine)['latest_date'].values[0]).strftime('%y-%m-%d %H:%M:%S')
    leagues = pd.read_sql_query('SELECT "League" FROM leagues', con = engine)['League'].values
    new_games = get_games(leagues, oldest_date)
    new_games = pd.DataFrame.from_dict([item["title"] for item in new_games])
    new_games.to_csv('data/new_games.csv', index = None)
    new_games = new_games.drop(columns = ['DateTime UTC__precision'])
    new_games = new_games.rename(columns = {'N GameInMatch' : 'NGameInMatch', 'DateTime UTC' : 'DateTime_UTC', 'Name' : 'Tournament'})
    new_games['DateTime_UTC'] = pd.to_datetime(new_games['DateTime_UTC'])
    new_dataset = pd.DataFrame.from_dict(get_competitive_match_data(new_games['RiotPlatformGameId'].values, new_games['RiotVersion']))
    new_features = get_features(new_dataset)
    model = init_model('models/winprob_soloq_competitive.json')
    preds = predict(model, new_features.drop(columns = ['match_id', 'winning_team']).values)
    new_predictions = pd.DataFrame()
    new_predictions['Id'] = new_dataset['match_id'] + '_' + new_features['minute'].astype(str)
    new_predictions['RiotPlatformGameId'] = new_dataset['match_id']
    new_predictions['Minute'] = new_features['minute']
    new_predictions['GoldDiff'] = new_dataset[[f'player{i}_gold' for i in range(1, 6)]].sum(axis = 1) - new_dataset[[f'player{i}_gold' for i in range(6, 11)]].sum(axis = 1)
    new_predictions['WinProbability'] = preds[:, 0]
    new_games.to_sql('competitive_games', engine, if_exists = 'append', index = None)
    new_predictions.to_sql('competitive_predictions', engine, if_exists = 'append', index = None)
    


if __name__ == '__main__':
    main()