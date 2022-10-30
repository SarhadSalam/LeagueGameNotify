import fileinput
import signal
import os
import settings
# import pylivestream.api as pls
from multiprocessing import Process
import psutil
import logging

class StreamHandler:
    def __init__(self):
        self.started_streaming = False
        self.stream_process = None

    def _generateScriptFile(self, userId, gameId):
        # not necessarily a string, and replace can only work on strings
        token_map = {
            "$USER_ID": str(userId),
            "$GAME_ID": str(gameId),
            "$LEAGUE_PATH": settings.LEAGUE_PATH,
            "$PARENT_DRIVE": settings.PARENT_DRIVE,
        }

        template = open(settings.TEMPLATE_SCRIPT_FILE)
        output = open(settings.GENERATED_SCRIPT_FILE, 'w+')

        for line in template:
            outLine = line
            for k, v in token_map.items():
                if k in line:
                    outLine = outLine.replace(k, v)

            output.write(outLine)

        template.close()
        output.close()

    def _runGeneratedScript(self):
        os.system(settings.GENERATED_SCRIPT_FILE)

    def tryStreaming(self, userId, gameId):
        # don't try to run stream, it's already running. instead change it
        # to a different user or end it
        if self.started_streaming:
            return
        self.started_streaming = True
        self.stream_process = Process(
            target=self._startSharingScreen, args=(userId, gameId))
        self.stream_process.start()

    def _startSharingScreen(self, userId, gameId):
        logging.info("Started sharing screen")
        self._generateScriptFile(userId, gameId)
        self._runGeneratedScript()
        pls.stream_screen(ini_file="pylivestream.ini",
                          websites=["twitch"], assume_yes=True)

    def _killLeagueClient(self):
        process_name = "League of Legends.exe"

        for p in psutil.process_iter():
            if p.name() == process_name:
                p.terminate()

        logging.info("Client Killing Complete")

    def _killStream(self):
        process_name = "ffmpeg.exe"

        for p in psutil.process_iter():
            if p.pid == self.stream_process.pid:
                p.terminate()
            if p.name() == process_name or p.name() == "Ffmpeg.exe":
                p.terminate()

        logging.info("Stream Killing Complete")

    def changeStream(self, game, userId):
        self._killLeagueClient()
        self._generateScriptFile(userId, gameId)
        self._runGeneratedScript()
        logging.info("Finished changing streams")

    def stopStreaming(self):
        if not self.started_streaming or not self.stream_process:
            logging.info("Stream process is NONE and/or not streaming but tried stopping")
            return
        self._killStream()
        self.stream_process = None

        # kill league client as well:
        self._killLeagueClient()
        self.started_streaming = False
        logging.info("League Client Killed")
