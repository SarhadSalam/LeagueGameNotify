import threading
import time
import sys
class PeriodicExecutor(threading.Thread):

    def __init__(self, sleep, func, *params):
        'Execute func(params) every "sleep" seconds'
        self.func = func
        self.params = params
        self.sleep = sleep
        threading.Thread.__init__(self, name="PeriodicExecutor")
        self.setDaemon(True)

    def run(self):
        while True:
            if self.func is None:
                sys.exit(0)
            self.func(*self.params)
            time.sleep(self.sleep)
