import datetime
import json
import time

import requests


class DataAnalysis(object):
    def __init__(self, telegramUrl):
        self.telegramUrl = telegramUrl
        self.localData = ""
        self.rowNumberOfDataToCheck = 3  # how many rows should be check in the local data


    def loadData(self):
        get_time = datetime.datetime.now()
        current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open("localData.json", "r") as L:
                tmpLocalData = L.read()
                self.localData = json.loads(tmpLocalData)

        except KeyError:
            print "DataAnalysis: (Error in load Local Data)" + str(current_time)

    def sendMsg(self, group, msg):
        url = self.telegramUrl + "?group=" + group + "&msg=" + msg
        ok = requests.get(url)
        return ok.text

    def analyzeData(self):
        ds.loadData()
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
                        print warniningCount

                if warniningCount > 1:
                    msg = str(patient) + " is critical with Heart rate: " + HRwithECG +\
                          " bpm and SpO2: " + BOwithIhealth
                    result = self.sendMsg("hospital", msg)
                    print msg

            with open('localData.json', 'w') as outfile:
                json.dump(allData, outfile)


if '__main__' == __name__:

    with open("RcConfig.json", "r") as f:
        tmpConf = f.read()
        conf = json.loads(tmpConf)
        telegramUrl = conf["telegram"]["sendMessageUrl"]

    ds = DataAnalysis(telegramUrl)

    while True:
        ds.analyzeData()
        time.sleep(1)



