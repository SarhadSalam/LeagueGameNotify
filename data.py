import settings
import requests
import api_calls
from summoner import Summoner
import json
import utils
import consts

DATA_FILE = "data.json"
CHAMPION_FILE = "champion.json"
SUMMONER_DATA = {}
CHAMPION_ID_TO_NAME = {}

def refreshSummonerData():
    SUMMONER_DATA.clear()
    print ("Refreshing Summoner Profile Data")
    for name in settings.SUMMONER_NAMES:
        url = api_calls.BASE_API_URL + api_calls.SUMMONER_API_URL.format(summonerName=name)
        response = requests.get(url, headers={consts.API_KEY_HEADER: settings.API_KEY})
        if response.status_code != 200:
            print("Failed to obtain data for" + name)
            print("Response Code:", response.status_code)
            continue
        SUMMONER_DATA[name] = Summoner()
        SUMMONER_DATA[name].SummonerDTO = response.json()
    print ("Completed Refreshing Summoner Profile Data")

    saveSummonerData()
    print("Dumped json output to", DATA_FILE)
    return SUMMONER_DATA

def loadSummonerData():
    SUMMONER_DATA.clear()
    try:
        with open(DATA_FILE, "r") as input_file:
            json_data = input_file.read()
            parsed = json.loads(json_data)
            for name in parsed:
                SUMMONER_DATA[name] = Summoner.fromJson(parsed[name])
    except FileNotFoundError:
        print("Could not find file", DATA_FILE)
    return SUMMONER_DATA

def saveSummonerData():
    with open (DATA_FILE, "w") as output_file:
        output_file.write(json.dumps(SUMMONER_DATA, indent=4, default=utils.toJson))

def loadChampionData():
    CHAMPION_ID_TO_NAME.clear()
    try:
        with open(CHAMPION_FILE, "r", encoding="utf8") as input_file:
            json_data = input_file.read()
            parsed = json.loads(json_data)
            data = parsed["data"]
            for name in data:
                id = int(data[name]["key"])
                CHAMPION_ID_TO_NAME[id] = name
    except FileNotFoundError:
        print("Could not find file", CHAMPION_FILE)

def getChampionName(championId):
    if championId in CHAMPION_ID_TO_NAME:
        return CHAMPION_ID_TO_NAME[championId]
    else:
        return "UNKNOWN"

if __name__ == "__main__":
    refreshSummonerData()
