import consts

class Summoner():
    def __init__(self):
        self.SummonerDTO = None
        self.CurrentGameInfo = None
        self.CurrentRank = None

    def updateCurrentGame(self, newGameInfo):
        if newGameInfo is None:
            self.CurrentGameInfo = None
            return False, False
        if self.CurrentGameInfo is None:
            self.CurrentGameInfo = newGameInfo
            return self.CurrentGameInfo["gameQueueConfigId"] == consts.RANKED_SOLO_QUEUE_ID, True
        if self.CurrentGameInfo["gameId"] != newGameInfo["gameId"]:
            # New Game Found
            self.CurrentGameInfo = newGameInfo
            return self.CurrentGameInfo["gameQueueConfigId"] == consts.RANKED_SOLO_QUEUE_ID, True
        return False, False

    def updateCurrentRank(self, newRank):
        if self.CurrentRank is None:
            self.CurrentRank = newRank
            return 3

        newTier, newDivision = newRank.split(" ")
        tier, division = self.CurrentRank.split(" ")

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

        if change != 0:
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
