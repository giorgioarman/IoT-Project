import datetime
import json
import time

import requests


class DataAnalysis(object):
    def __init__(self, telegramUrl):
        self.telegramUrl = telegramUrl
        self.localData = ""
        self.rowNumberOfDataToCheck = 3  # how many rows should be check in the local data
        self.msgSent = dict()

    def loadData(self):
        get_time = datetime.datetime.now()
        current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
        print current_time
        try:
            with open("localData.json", "r") as L:
                tmpLocalData = L.read()
                self.localData = json.loads(tmpLocalData)
            if len(self.msgSent) == 0:
                localDataJson = self.localData.keys()
                for item in localDataJson:
                    self.msgSent[item] = {'flag': False, 'time': time.time()}

        except KeyError:
            print "DataAnalysis: (Error in load Local Data)" + str(current_time)

    def sendMsg(self, group, msg):
        url = self.telegramUrl + "?group=" + group + "&msg=" + msg
        ok = requests.get(url)
        return ok.text

    def analyzeData(self):

        self.loadData()
        self.trigger()
        allData = self.localData
        if allData is not None:
            # check data for every patient
            for patient in allData:
                dataPatient = allData[str(patient)]
                 # check the last rows that we declare in the init
                lastData = dataPatient[-self.rowNumberOfDataToCheck:]
                warniningCount = 0
                for item in lastData:
                    # check there is a new data in local file or not
                    if int(item["ReadDataCount"]) == self.rowNumberOfDataToCheck:
                        print "there is no new data"
                        break
                    if int(item["ReadDataCount"]) == 0:
                        item["ReadDataCount"] = 3
                        lastData[1]["ReadDataCount"] = 2
                        lastData[2]["ReadDataCount"] = 1
                        break
                    else:
                        HRwithIhealth = item["HRwithIhealth"]
                        BOwithIhealth = item["BOwithIhealth"]
                        HRwithECG = item["HRwithECG"]

                        # check the difference between data collect from two sensor
                        if abs(HRwithECG - HRwithIhealth) > 10:
                            print "data from iHealth sensor and ECG are not the same"
                        else:
                            # ********________--------
                            # check data with treshold
                            # --------________********
                            if HRwithECG < 54 or HRwithECG > 78:
                                if BOwithIhealth < 80:
                                    warniningCount += 1

                        item["ReadDataCount"] = int(item["ReadDataCount"]) + 1


                # control if in the 60 seconds ago the message is sent OR not
                if warniningCount > 1 and not self.msgSent[patient]['flag']:
                    msg = str(patient) + " is critical with Heart rate: " + str(HRwithECG) +\
                          " bpm and SpO2: " + str(BOwithIhealth)
                    result = self.sendMsg("hospital", msg)
                    self.msgSent[patient]['flag'] = True
                    self.msgSent[patient]['time'] = time.time()
                    print msg

            with open('localData.json', 'w') as outfile:
                json.dump(allData, outfile)

    def trigger(self):
        for item in self.msgSent:
            if abs(int(self.msgSent[item]['time']) - time.time()) > 60:
                self.msgSent[item]['flag'] = False


if '__main__' == __name__:

    with open("RcConfig.json", "r") as f:
        tmpConf = f.read()
        conf = json.loads(tmpConf)
        telegramUrl = conf["telegram"]["sendMessageUrl"]

    ds = DataAnalysis(telegramUrl)

    while True:
        ds.analyzeData()
        time.sleep(3)



