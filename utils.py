import consts

# json fallback
def toJson(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__

class ColorCodes():
    GREEN = "```diff\n+ {msg}\n```"
    YELLOW = "```fix\n{msg}\n```"
    RED = "```diff\n- {msg}\n```"

def applyColorToMsg(msg, color):
    if color is None:
        return msg
    return color.format(msg=msg)

def getRankValue(rank):
    if rank is None:
        return 0
    tier = consts.TIERS.index(rank["tier"])
    division = consts.DIVISIONS.index(rank["division"])
    lp = int(rank["lp"])
    tierScore = (len(consts.DIVISIONS) + 1) * 100
    divisionScore = 100
    return tier * tierScore + division * divisionScore + lp

def getSummonerRankValue(summoner):
    if summoner is None:
        return 0
    return getRankValue(summoner.CurrentRank)
