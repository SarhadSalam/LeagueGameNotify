import settings
import requests
import api_calls
from summoner import Summoner
import json
import utils
import consts

DATA_FILE = "data.json"
CHAMPION_FILE = "champion.json"
CRINGE_NAMES_FILE = "cringe_names.txt"
SUMMONER_DATA = {}
CHAMPION_ID_TO_NAME = {}
CHAMPION_NAME_TO_CRINGE_NAME = {}

def refreshSummonerData():
    SUMMONER_DATA.clear()
    print ("Refreshing Summoner Profile Data")
    for name in settings.SUMMONER_NAMES:
        url = api_calls.BASE_API_URL + api_calls.SUMMONER_API_URL.format(summonerName=name)
        response = api_calls.call_api(url)
        if response is None or response.status_code != 200:
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
        return None
    return SUMMONER_DATA

def saveSummonerData():
    with open (DATA_FILE, "w") as output_file:
        output_file.write(json.dumps(SUMMONER_DATA, indent=4, default=utils.toJson))

def loadChampionData():
    CHAMPION_ID_TO_NAME.clear()
    CHAMPION_NAME_TO_CRINGE_NAME.clear()
    try:
        with open(CHAMPION_FILE, "r", encoding="utf8") as input_file:
            json_data = input_file.read()
            parsed = json.loads(json_data)
            data = parsed["data"]
            for name in data:
                id = int(data[name]["key"])
                CHAMPION_ID_TO_NAME[id] = name
    except FileNotFoundError:
        print("Could not find file", CHAMPION_FILE, "so champ names will show as UNKNOWN")
    try:
        with open(CRINGE_NAMES_FILE, "r", encoding="utf8") as input_file:
            lines = input_file.readlines()
            for line in lines:
                names = line.split(" = ")
                realName, cringeName = names[0], names[1]
                if cringeName[-1] == '\n':
                    cringeName = cringeName[:-1]
                CHAMPION_NAME_TO_CRINGE_NAME[realName] = cringeName
    except FileNotFoundError:
        print("Could not find file", CRINGE_NAMES_FILE, "so not using substituted names")

def getChampionName(championId):
    if championId in CHAMPION_ID_TO_NAME:
        championName = CHAMPION_ID_TO_NAME[championId]
        if championName in CHAMPION_NAME_TO_CRINGE_NAME:
            return CHAMPION_NAME_TO_CRINGE_NAME[championName]
        else:
            return championName
    else:
        return "UNKNOWN"

if __name__ == "__main__":
    refreshSummonerData()
