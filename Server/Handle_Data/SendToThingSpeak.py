import datetime
import json
import time

import requests
from paho.mqtt import publish


class ThingSpeak(object):
    def __init__(self, rcUrl):
        self.ThingSpeak_url = ""
        self.ThingSpeak_Api_key = ""
        self.ThingSpeak_channelID = ""
        self.ThingSpeak_Connection_Type = ""
        self.ThingSpeak_Port = 0

        self.topic = ""
        self.RcURL = rcUrl

    def loadTsConfig(self):
        try:
            tmpTs = requests.get(self.RcURL + "thingspeak")
            thingSpeakData = json.loads(tmpTs.text)
        except ValueError:
            print "ThingSpeak: There was an error in connecting to the Resource Catalog" + str(ValueError)

        self.ThingSpeak_url = thingSpeakData["ThingSpeak_url"]
        self.ThingSpeak_Port = thingSpeakData["ThingSpeak_Port"]
        self.ThingSpeak_Connection_Type = thingSpeakData["ThingSpeak_Connection_Type"]
        self.ThingSpeak_Api_key = thingSpeakData["ThingSpeak_Api_key"]

    def loadTsChannelID(self, paintentId):
        try:
            tmpChn = requests.get(self.RcURL + paintentId)
            paitentData = json.loads(tmpChn.text)
            self.ThingSpeak_channelID = paitentData["ThingSpeak"]['ThingSpeak_channelID']
        except:
            print "ThingSpeak: There was an error in connecting to the Resource Catalog"

    def sendSpo2Data(self, msg, patientId):
        try:
            HRwithIhealth = msg["HRwithIhealth"]
            HRwithECG = msg["HRwithECG"]
            BOwithIhealth = msg["BOwithIhealth"]
            DateInsert = msg["DateInsert"]

            # Load ThingSpeak Data and channel id

            self.loadTsChannelID(patientId)

            self.topic = "channels/" + self.ThingSpeak_channelID + "/publish/" + self.ThingSpeak_Api_key

            payload = "&field1=" + str(BOwithIhealth) +\
                      "&field2=" + str(HRwithIhealth) +\
                      "&field3=" + str(HRwithECG) +\
                      "&field4=" + str(DateInsert)
            # publish
            publish.single(self.topic, payload, hostname=self.ThingSpeak_url,
                           transport=self.ThingSpeak_Connection_Type, port=self.ThingSpeak_Port)
            time.sleep(2)
        except:
            print "error"
        return True


if '__main__' == __name__:

    with open("RcConfig.json", "r") as f:
        tmpConf = f.read()
        conf = json.loads(tmpConf)
        RcURL = conf["ResourseCatalogInfo"]["url"]
        if not str(RcURL).endswith('/'):
            RcURL = str(RcURL) + "/"

    TsClass = ThingSpeak(RcURL)
    TsClass.loadTsConfig()
    while True:
        try:
            get_time = datetime.datetime.now()
            current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")

            # Read all data from Local file
            with open("localData.json", "r") as L:
                tmpLocalData = L.read()
                localData = json.loads(tmpLocalData)
            #     Split data for every patient
            for Patient in localData.keys():
                localDataJson = localData[Patient]
                for data in localDataJson:
                    # Check if data was sent to Thing speak or Not
                    if int(data["ThingSpeak"]) == 0:
                        # publish to thingspeak
                        isSentToThingSpeak = TsClass.sendSpo2Data(data, Patient)
                        if isSentToThingSpeak:
                            data["ThingSpeak"] = 1
                            print ("SubscribeData: (successfully) sent to ThingSpeak at time : " + str(current_time))
            # update the local data (the flag "ThingSpeak" was modified when the data was successfully published)
            with open('localData.json', 'w') as outfile:
                json.dump(localData, outfile)

        except KeyError:
            print"Error in loading data or main part of application "

        time.sleep(0.2)
