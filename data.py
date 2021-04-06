import settings
import requests
import api_calls
from summoner import Summoner
import json
import utils
import consts
import random

DATA_FILE = "data.json"
CHAMPION_FILE = "champion.json"
CRINGE_NAMES_FILE = "cringe_names.txt"
NOTIFY_DATA_FILE = "notifyMe.json"

SUMMONER_DATA = {}
CHAMPION_ID_TO_NAME = {}
CHAMPION_NAME_TO_CRINGE_NAME = {}
NOTIFY_DATA = {}

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
        SUMMONER_DATA[name.lower()] = Summoner()
        SUMMONER_DATA[name.lower()].SummonerDTO = response.json()
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
                SUMMONER_DATA[name.lower()] = Summoner.fromJson(parsed[name])
    except FileNotFoundError:
        print("Could not find file", DATA_FILE)
        return None
    return SUMMONER_DATA

def saveSummonerData():
    with open (DATA_FILE, "w") as output_file:
        output_file.write(json.dumps(SUMMONER_DATA, indent=4, default=utils.toJson))

def isKnownSummoner(summonerName):
    if summonerName is None:
        return "No Summoner Name Found"
    if summonerName.lower() not in SUMMONER_DATA:
        return summonerName + " is not one of the boiis"
    return True

def getSummonerName(summonerName):
    name = summonerName.lower()
    if name in SUMMONER_DATA:
        return SUMMONER_DATA[name].SummonerDTO["name"]
    return None

def getSummoner(summonerName):
    name = summonerName.lower()
    if name in SUMMONER_DATA:
        return SUMMONER_DATA[name]
    return None

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

def loadNotifyData():
    global NOTIFY_DATA
    NOTIFY_DATA.clear()
    try:
        with open(NOTIFY_DATA_FILE, "r") as input_file:
            json_data = input_file.read()
            NOTIFY_DATA = json.loads(json_data)
    except FileNotFoundError:
        print("Could not find file", NOTIFY_DATA_FILE)
        return None
    return NOTIFY_DATA

def saveNotifyData():
    with open (NOTIFY_DATA_FILE, "w") as output_file:
        output_file.write(json.dumps(NOTIFY_DATA, indent=4, default=utils.toJson))

def getNotifyListForSummoner(summonerName):
    if summonerName in NOTIFY_DATA:
        return NOTIFY_DATA[summonerName]
    else:
        return None

def addToNotifyList(summonerName, entry):
    if (msg := isKnownSummoner(summonerName)) is not True:
        return msg
    if summonerName not in NOTIFY_DATA:
        NOTIFY_DATA[summonerName] = []
    if entry in NOTIFY_DATA[summonerName]:
        return "You are already simping for " + summonerName
    else:
        NOTIFY_DATA[summonerName].append(entry)
    saveNotifyData()
    return True

def removeFromNotifyList(summonerName, entry):
    if (msg := isKnownSummoner(summonerName)) is not True:
        return msg
    elif summonerName not in NOTIFY_DATA or entry not in NOTIFY_DATA[summonerName]:
        return "You are not simping for " + summonerName + " >:("
    else:
        NOTIFY_DATA[summonerName].remove(entry)
    saveNotifyData()
    return True

def getNotifyList(user):
    summoners = []
    for summoner in NOTIFY_DATA:
        if user in NOTIFY_DATA[summoner]:
            summoners.append(summoner)
    return summoners

def removeFromAllNotifyList(user):
    for summoner in NOTIFY_DATA:
        if user in NOTIFY_DATA[summoner]:
            NOTIFY_DATA[summoner].remove(user)
    saveNotifyData()

def addToAllNotifyList(user):
    for summoner in settings.SUMMONER_NAMES:
        if summoner not in NOTIFY_DATA:
            NOTIFY_DATA[summoner] = []
        if user not in NOTIFY_DATA[summoner]:
            NOTIFY_DATA[summoner].append(user)
    saveNotifyData()

def getRandomSummoner(skipList=None):
    if skipList is None:
        return random.choice(settings.SUMMONER_NAMES)
    else:
        names = [name for name in settings.SUMMONER_NAMES]
        for entry in skipList:
            if entry in names:
                names.remove(entry)
        return random.choice(names)

def getDiscordIdFromSummonerName(summonerName):
    if summonerName in settings.DISCORD_IDS:
        return settings.DISCORD_IDS[summonerName]
    return None

def getSummonerNameFromName(name):
    if name in settings.NAME_IDS:
        return settings.NAME_IDS[name]
    return None

def load():
    loadSummonerData()
    loadChampionData()
    loadNotifyData()

if __name__ == "__main__":
    refreshSummonerData()
