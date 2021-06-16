API_ADDR = "http://api.dbarasti.com:8080/"
headers = {"accept": "application/json", "Content-Type": "application/json"}
import requests
import datetime
from config import *
import json

def get_date_from_string(str):
    return datetime.datetime.strptime(str.replace("Z",""), "%Y-%m-%dT%H:%M:%S.%f")

now = datetime.datetime.now()

# Request tournaments
tournaments_response = requests.get(API_ADDR+"tournament", headers=headers).json()

available_tournaments = {}

if tournaments_response['category'] == 'success':
    tournaments = tournaments_response['data']

    for t in tournaments:
        tournament_subscription_ending = get_date_from_string(t['end_subscriptions_date'])
        if (tournament_subscription_ending-now).total_seconds() > 0:
            print("\nAvailable tournament:")
            print(f"\tGame type: {t['game_type']}")
            print(f"\tID: {t['id']}")
            print(f"\tMatches start at: {get_date_from_string(t['start_matches_date'])}")
            print(f"\tSubscriptions start at: {get_date_from_string(t['start_subscriptions_date'])}")
            available_tournaments[t['id']] = t

    value = input("\nInsert the ID of the tournament of which you want to subscribe: ")

    if value in available_tournaments:
        selected_tournament = available_tournaments[value]
        for agent in AGENTS:

            agent_data = {
                          "player_id": agent[0],
                          "tournament_id": selected_tournament['id']
                        }
            registration_response = requests.post(API_ADDR+"registration", headers=headers, data=json.dumps(agent_data)).json()
            print(f"Check: {requests.get(API_ADDR+'registration/check', headers=headers, params=agent_data).json()['status'] == 200}")




