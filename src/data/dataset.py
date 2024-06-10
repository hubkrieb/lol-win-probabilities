from src.data.utils import riot_api_request
import pandas as pd
import mwrogue.esports_client as ec

RIOT_API_KEY = 'RGAPI-faec5e54-6e5a-4dd8-a3ab-fc8746fdae31'

server_mapping = {'euw1' : 'europe', 'na1' : 'americas', 'kr' : 'asia'}

def get_puuids(server, tier):

    url = f'https://{server}.api.riotgames.com/lol/league/v4/{tier}leagues/by-queue/RANKED_SOLO_5x5?api_key={RIOT_API_KEY}'

    response = riot_api_request(url)
    data = response.json()

    def get_puuid(summonerId):
        response = riot_api_request(f'https://{server}.api.riotgames.com/lol/summoner/v4/summoners/{summonerId}?api_key={RIOT_API_KEY}')
        data = response.json()
        return data['puuid']

    puuids = [get_puuid(player['summonerId']) for player in data['entries']]

    return puuids

def get_match_ids(server, puuids, count, start_time):

    match_ids = []

    for puuid in puuids:
        url = f'https://{server_mapping[server]}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?startTime={start_time}&queue=420&type=ranked&start=0&count={count}&api_key={RIOT_API_KEY}'
        response = riot_api_request(url)
        data = response.json()
        match_ids += data
    
    return list(set(match_ids))

def get_soloq_match_data(match_ids, existing_dataset = None):

    if existing_dataset is not None:
        dataset = existing_dataset.to_dict('records')
    else:
        dataset = []

    for i, match_id in enumerate(match_ids):
        print(match_id)
        server = match_id.split('_')[0].lower()
        match_url = f'https://{server_mapping[server]}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={RIOT_API_KEY}'
        try:
            match_response = riot_api_request(match_url)
        except Exception as e:
            print(e)
        else:
            match_data = match_response.json()
            try:
                end_of_game_result = match_data['info']['endOfGameResult']
            except:
                end_of_game_result = 'GameComplete'
            if end_of_game_result == 'GameComplete' and match_data['info']['participants'][0]['gameEndedInEarlySurrender'] == False and match_data['info']['participants'][0]['gameEndedInSurrender'] == False and match_data['info']['gameDuration'] > 300:
                winning_team = match_data['info']['teams'][0]['teamId'] // 100 if match_data['info']['teams'][0]['win'] else match_data['info']['teams'][1]['teamId'] // 100
                champion_picks = {}
                for i in range(10):
                    champion_picks[f'player{i + 1}_champion'] = match_data['info']['participants'][i]['championName']

                timeline_url = f'https://{server_mapping[server]}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline?api_key={RIOT_API_KEY}'
                timeline_response = riot_api_request(timeline_url)
                timeline = timeline_response.json()
                timeline_data = get_match_timeline_data(match_id, timeline, winning_team, champion_picks)
                dataset += timeline_data
            if i % 100 == 0:
                dataset_df = pd.DataFrame.from_dict(dataset)
                dataset_df.to_csv('data/dataset.csv', index = None)
    return dataset

def get_competitive_match_data(rpg_ids, riot_versions, existing_dataset = None):
    
    if existing_dataset is not None:
        dataset = existing_dataset.to_dict('records')
    else:
        dataset = []

    client = ec.EsportsClient('lol')

    for i in range(len(rpg_ids)):
        rpg_id = rpg_ids[i]
        riot_version = riot_versions[i]
        if rpg_id is not None and riot_version is not None:
            print(rpg_id)
            riot_version = int(riot_version)
            timeline = {}
            data, timeline['info'] = client.get_data_and_timeline(rpg_id, riot_version)
            winning_team = 1 if data['teams'][0]['win'] else 2
            champion_picks = {}
            for i in range(10):
                champion_picks[f'player{i + 1}_champion'] = data['participants'][i]['championName']
            timeline_data = get_match_timeline_data(rpg_id, timeline, winning_team, champion_picks)
            dataset += timeline_data
        else:
            print('None RiotPlatformGameId')
    return dataset


def get_match_timeline_data(match_id, timeline, winning_team, champion_picks):
        
        """Base Respawn Wait time (BRW)"""
        brw = [6, 6, 8, 8, 10, 12, 16, 21, 26, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50, 52.5]

        def get_tif(timestamp):
            """Get the Time Increase Factor (TIF) for Respawn Wait time"""
            minutes = timestamp // 60000
            if minutes < 15:
                tif = 0
            elif minutes < 30:
                tif = 0 + 2 * (minutes - 15) * 0.425 / 100
            elif minutes < 45:
                tif = 12.75 + 2 * (minutes - 30) * 0.3 / 100
            else:
                tif = 21.75 + 2 * (minutes - 45) * 1.45 / 100
            return tif

        rows = []

        respawn_tracker = {'player1_respawn' : 0, 'player2_respawn' : 0, 'player3_respawn' : 0, 'player4_respawn' : 0, 'player5_respawn' : 0, 'player6_respawn' : 0, 'player7_respawn' : 0, 'player8_respawn' : 0, 'player9_respawn' : 0, 'player10_respawn' : 0}
        turret_tracker = {'team1_outerTurret' : 0, 'team1_innerTurret' : 0, 'team1_baseTurret' : 0, 'team1_nexusTurret' : 0, 'team2_outerTurret' : 0, 'team2_innerTurret' : 0, 'team2_baseTurret' : 0, 'team2_nexusTurret' : 0}
        inhibitor_respawn_tracker = {'team1_topInhibitor' : 0, 'team1_midInhibitor' : 0, 'team1_botInhibitor' : 0, 'team2_topInhibitor' : 0, 'team2_midInhibitor' : 0, 'team2_botInhibitor' : 0}
        dragon_tracker = {'team1_airDragon' : 0, 'team1_fireDragon' : 0, 'team1_hextechDragon' : 0, 'team1_chemtechDragon' : 0, 'team1_earthDragon' : 0, 'team1_waterDragon' : 0, 'team2_airDragon' : 0, 'team2_fireDragon' : 0, 'team2_hextechDragon' : 0, 'team2_chemtechDragon' : 0, 'team2_earthDragon' : 0, 'team2_waterDragon' : 0}
        dragon_soul_tracker = {'team1_airDragonSoul' : 0, 'team1_fireDragonSoul' : 0, 'team1_hextechDragonSoul' : 0, 'team1_chemtechDragonSoul' : 0, 'team1_earthDragonSoul' : 0, 'team1_waterDragonSoul' : 0, 'team2_airDragonSoul' : 0, 'team2_fireDragonSoul' : 0, 'team2_hextechDragonSoul' : 0, 'team2_chemtechDragonSoul' : 0, 'team2_earthDragonSoul' : 0, 'team2_waterDragonSoul' : 0}
        elder_dragon_tracker = {'team1_elderDragon' : 0, 'team2_elderDragon' : 0}
        elder_buff_tracker = {'player1_elderDragon' : 0, 'player2_elderDragon' : 0, 'player3_elderDragon' : 0, 'player4_elderDragon' : 0, 'player5_elderDragon' : 0, 'player6_elderDragon' : 0, 'player7_elderDragon' : 0, 'player8_elderDragon' : 0, 'player9_elderDragon' : 0, 'player10_elderDragon' : 0}
        nashor_tracker = {'team1_nashor' : 0, 'team2_nashor' : 0}
        nashor_buff_tracker = {'player1_nashor' : 0, 'player2_nashor' : 0, 'player3_nashor' : 0, 'player4_nashor' : 0, 'player5_nashor' : 0, 'player6_nashor' : 0, 'player7_nashor' : 0, 'player8_nashor' : 0, 'player9_nashor' : 0, 'player10_nashor' : 0}
        grub_tracker = {'team1_grub' : 0, 'team2_grub' : 0}
        herald_tracker = {'team1_herald' : 0, 'team2_herald' : 0}

        current_stats = {}
        current_stats['match_id'] = match_id
        current_stats['winning_team'] = winning_team
        # Do not consider the last frame that corresponds to end game (nothing to predict and high bias with nexus turret destroyed?)
        for frame in timeline['info']['frames'][:-1]:
            current_stats['timestamp'] = frame['timestamp']
            for event in frame['events']:
                if event['type'] == 'LEVEL_UP':
                    current_stats[f'player{event["participantId"]}_level'] = event['level']
                elif event['type'] == 'CHAMPION_KILL':
                    victim_id = event['victimId']
                    victim_level = current_stats[f'player{victim_id}_level']
                    kill_timestamp = event['timestamp']
                    respawn_time = (brw[victim_level - 1] + brw[victim_level - 1] * get_tif(kill_timestamp)) * 1000
                    respawn_tracker[f'player{int(victim_id)}_respawn'] = kill_timestamp + respawn_time
                    # Remove Nashor and Elder Dragon buffs
                    nashor_buff_tracker[f'player{int(victim_id)}_nashor'] = 0
                    elder_buff_tracker[f'player{int(victim_id)}_elderDragon'] = 0
                elif event['type'] == 'BUILDING_KILL':
                    if event['buildingType'] == 'TOWER_BUILDING':
                        turret_type = event['towerType'].split('_')[0].lower()
                        turret_tracker[f'team{event["teamId"] // 100}_{turret_type}Turret'] += 1
                    elif event['buildingType'] == 'INHIBITOR_BUILDING':
                        lane = event['laneType'].split('_')[0].lower()
                        inhibitor_respawn_tracker[f'team{event["teamId"] // 100}_{lane}Inhibitor'] = event['timestamp'] + 5 * 60000
                elif event['type'] == 'ELITE_MONSTER_KILL':
                    if event['monsterType'] == 'DRAGON':
                        if event['monsterSubType'] == 'ELDER_DRAGON':
                            elder_dragon_tracker[f'team{event["killerTeamId"] // 100}_elderDragon'] = event['timestamp'] + 150 * 1000
                            # Check players alive to give buff
                            if event["killerTeamId"] == 100:
                                for i in range(1, 6):
                                    if respawn_tracker[f'player{i}_respawn'] <= event['timestamp']:
                                        elder_buff_tracker[f'player{i}_elderDragon'] = event['timestamp'] + 150 * 1000
                            elif event["killerTeamId"] == 200:
                                for i in range(6, 11):
                                    if respawn_tracker[f'player{i}_respawn'] <= event['timestamp']:
                                        elder_buff_tracker[f'player{i}_elderDragon'] = event['timestamp'] + 150 * 1000
                        else:
                            dragon_type = event['monsterSubType'].split('_')[0].lower()
                            dragon_tracker[f'team{event["killerTeamId"] // 100}_{dragon_type}Dragon'] += 1
                        if dragon_tracker[f'team{event["killerTeamId"] // 100}_airDragon'] + dragon_tracker[f'team{event["killerTeamId"] // 100}_fireDragon'] + dragon_tracker[f'team{event["killerTeamId"] // 100}_hextechDragon'] + dragon_tracker[f'team{event["killerTeamId"] // 100}_chemtechDragon'] + dragon_tracker[f'team{event["killerTeamId"] // 100}_earthDragon'] + dragon_tracker[f'team{event["killerTeamId"] // 100}_waterDragon'] == 4:
                            dragon_soul_tracker[f'team{event["killerTeamId"] // 100}_{dragon_type}DragonSoul'] = 1
                    elif event['monsterType'] == 'BARON_NASHOR':
                        nashor_tracker[f'team{event["killerTeamId"] // 100}_nashor'] = event['timestamp'] + 180 * 1000
                        # Check players alive to give buff
                        if event["killerTeamId"] == 100:
                                for i in range(1, 6):
                                    if respawn_tracker[f'player{i}_respawn'] <= event['timestamp']:
                                        nashor_buff_tracker[f'player{i}_nashor'] = event['timestamp'] + 180 * 1000
                        elif event["killerTeamId"] == 200:
                            for i in range(6, 11):
                                if respawn_tracker[f'player{i}_respawn'] <= event['timestamp']:
                                    nashor_buff_tracker[f'player{i}_nashor'] = event['timestamp'] + 180 * 1000
                    elif event['monsterType'] == 'HORDE':
                        if event['killerTeamId'] in [100, 200]:
                            grub_tracker[f'team{event["killerTeamId"] // 100}_grub'] += 1
                    elif event['monsterType'] == 'RIFTHERALD':
                        if event['killerTeamId'] in [100, 200]:
                            herald_tracker[f'team{event["killerTeamId"] // 100}_herald'] = 1
                elif event['type'] == 'ITEM_DESTROYED':
                    if event['itemId'] == 3513:
                        herald_tracker[f'team{int(event["participantId"] > 5) + 1}_herald'] = 0
                    

            participantFrames = frame['participantFrames']

            for i in range(1, 11):
                participant = str(i)
                current_stats[f'player{participant}_gold'] = participantFrames[participant]['totalGold']
                current_stats[f'player{participant}_xp'] = participantFrames[participant]['xp']
                current_stats[f'player{participant}_level'] = participantFrames[participant]['level']

                if respawn_tracker[f'player{int(participant)}_respawn'] > frame['timestamp']:
                    current_stats[f'player{participant}_isAlive'] = 0
                else:
                    current_stats[f'player{participant}_isAlive'] = 1
            rows.append({**current_stats, **champion_picks, **respawn_tracker, **turret_tracker, **inhibitor_respawn_tracker, **dragon_tracker, **dragon_soul_tracker, **elder_dragon_tracker, **elder_buff_tracker, **nashor_tracker, **nashor_buff_tracker, **herald_tracker, **grub_tracker})
        return rows