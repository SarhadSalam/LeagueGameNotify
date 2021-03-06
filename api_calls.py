import consts
import settings
import requests

BASE_API_URL="https://na1.api.riotgames.com"
SUMMONER_API_URL = "/lol/summoner/v4/summoners/by-name/{summonerName}"
SPECTATOR_API_URL = "/lol/spectator/v4/active-games/by-summoner/{encryptedSummonerId}"
LEAGUE_API_URL = "/lol/league/v4/entries/by-summoner/{encryptedSummonerId}"
MATCH_API_URL = "/lol/match/v4/matches/{matchId}"
CLASH_API_URI = "/lol/clash/v1/tournaments"
CHAMPION_MASTERY_ALL_URI = "/lol/champion-mastery/v4/champion-masteries/by-summoner/{encryptedSummonerId}"
CHAMPION_MASTERY_CHAMP_URI = "/lol/champion-mastery/v4/champion-masteries/by-summoner/{encryptedSummonerId}/by-champion/{championId}"
MATCH_HISTORY_URI = "https://matchhistory.na.leagueoflegends.com/en/#match-details/NA1/{gameId}/{playerCode}"

MMR_URI = "https://na.whatismymmr.com/api/v1/summoner?name={summonerName}"

def call_api(url):
    try:
        if not url.startswith("https:"):
            url = BASE_API_URL + url
        response = requests.get(url, headers={consts.API_KEY_HEADER: settings.API_KEY})
        return response
    except:
        print("Connection Error. Skipping Request")
        return None
