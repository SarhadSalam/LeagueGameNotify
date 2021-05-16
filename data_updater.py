import data
import api_calls
import json

CURRENT_VERSION = None

def getLatestDDVersion():
    response = api_calls.call_api(api_calls.VERSION_URL)
    if response and response.status_code == 200:
        return response.json()[0]
    else:
        return None

def getCurrentDDVersion():
    global CURRENT_VERSION
    if CURRENT_VERSION is not None:
        return CURRENT_VERSION
    try:
        filename = data.CHAMPION_FILE
        with open(filename, "r") as input_file:
            json_data = input_file.read()
            parsed = json.loads(json_data)
            version = parsed["version"]
            CURRENT_VERSION = version
            return version
    except FileNotFoundError:
        print("Could not find file", filename)
        return None

def updateDDVersionFiles(forceUpdate=False):
    status = ""
    latestVersion = getLatestDDVersion()
    if latestVersion is None:
        status = "Error obtaining latest version"
        print(status)
        return False, status
    if not forceUpdate:
        currentVersion = getCurrentDDVersion()
        if latestVersion == currentVersion:
            status = "No new version available"
            print(status)
            return False, status
    url = api_calls.CHAMPION_DATA_URL.format(version=latestVersion)
    response = api_calls.call_api(url)
    if response and response.status_code == 200:
        with open (data.CHAMPION_FILE, "w") as output_file:
            output_file.write(json.dumps(response.json(), indent=4))
        CURRENT_VERSION = latestVersion
        reloadChampionData()
        status = "Updated DD to version " + CURRENT_VERSION
        print(status)
        return True, status

def reloadSummonerData(refresh=False):
    return  # Not yet supported
    if refresh:
        data.refreshSummonerData()
    else:
        data.loadSummonerData()

def reloadChampionData():
    data.loadChampionData()

def reloadData(refresh=False):
    reloadSummonerData(refresh)
    reloadChampionData()
