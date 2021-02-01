import consts

class Summoner():
    def __init__(self):
        self.SummonerDTO = None
        self.CurrentGameInfo = None
        self.CurrentRank = None

    def updateCurrentGame(self, newGameInfo):
        ret_status = {"notifyStart":False, "notifyEnd":None, "requestSave":False}
        if newGameInfo is None:
            if self.CurrentGameInfo != None and self.CurrentGameInfo["gameQueueConfigId"] == consts.RANKED_SOLO_QUEUE_ID:
                # Ranked Game End
                ret_status["notifyEnd"] = self.CurrentGameInfo["gameId"]
            self.CurrentGameInfo = None
        elif self.CurrentGameInfo is None:
            self.CurrentGameInfo = newGameInfo
            ret_status["notifyStart"] = self.CurrentGameInfo["gameQueueConfigId"] == consts.RANKED_SOLO_QUEUE_ID
            ret_status["requestSave"] = True
        elif self.CurrentGameInfo["gameId"] != newGameInfo["gameId"]:
            # New Game Found
            ret_status["notifyStart"] = newGameInfo["gameQueueConfigId"] == consts.RANKED_SOLO_QUEUE_ID
            ret_status["notifyEnd"] = self.CurrentGameInfo["gameId"] if self.CurrentGameInfo["gameQueueConfigId"] == consts.RANKED_SOLO_QUEUE_ID else None
            ret_status["requestSave"] = True
            self.CurrentGameInfo = newGameInfo
        return ret_status

    def updateCurrentRank(self, newRank):
        if self.CurrentRank is None:
            self.CurrentRank = newRank
            return 3

        newTier, newDivision = newRank["tier"], newRank["division"]
        tier, division = self.CurrentRank["tier"], self.CurrentRank["division"]

        change = 0
        if consts.TIERS.index(tier) == consts.TIERS.index(newTier):
            if consts.DIVISIONS.index(division) == consts.DIVISIONS.index(newDivision):
                change = 0
            elif consts.DIVISIONS.index(division) < consts.DIVISIONS.index(newDivision):
                change = 1
            else:
                change = -1
        elif consts.TIERS.index(tier) < consts.TIERS.index(newTier):
            change = 2
        else:
            change = -2

        self.CurrentRank = newRank
        return change

    def toJson(self):
        return self.__dict__

    @staticmethod
    def fromJson(jsonObj):
        summoner = Summoner()
        summoner.SummonerDTO = jsonObj["SummonerDTO"]
        summoner.CurrentGameInfo = jsonObj["CurrentGameInfo"]
        summoner.CurrentRank = jsonObj["CurrentRank"]
        return summoner

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)
