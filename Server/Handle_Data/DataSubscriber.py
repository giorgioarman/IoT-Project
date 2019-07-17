import datetime
import time
import paho.mqtt.client as mqtt
import json
import requests


class SubscribeData(object):
    iHealthDataCounter = 0  # type: int
    iHealthData = ""  # type: str
    EcgDataCounter = 0  # type: int
    EcgData = ""  # type: str

    def __init__(self, client, rcURL):
        self.client = client
        self.rcURL = rcURL
        self.bothSensorDataReceived = False
        self.iHealthData = ""
        self.iHealthDataCounter = 0
        self.EcgData = ""
        self.EcgDataCounter = 0

    @staticmethod
    def on_connect(client, userdata, flags, rc):
        get_time = datetime.datetime.now()
        current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
        print ('Subscribe Data: Connecting to Broker has done successfully at time: ' + str(current_time))
        return str(rc)

    @staticmethod
    def on_subscribe(client, userdata, mid, granted_qos):
        get_time = datetime.datetime.now()
        current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
        print ('SubscribeData: (successfully) Started to subscribe '+str(mid) + 'with QoS' + str(granted_qos)
               + ' at time: ' + str(current_time))
        return str(mid)

    @classmethod
    def on_message(self, client, userdata, msg):
        get_time = datetime.datetime.now()
        current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
        messageDataJson = msg.payload.decode("utf-8")
        messageData = json.loads(messageDataJson)

        if messageData["subject"] == "spo2":
            self.iHealthData = messageData
            counter = self.iHealthDataCounter + 1
            self.iHealthDataCounter = counter
            print("SubscribeData: (Received Data from iHealth) " + str(messageData) + " at time : " + str(current_time))
        elif messageData["subject"] == "ECG":
            self.EcgData = messageData
            counter = self.EcgDataCounter + 1
            self.EcgDataCounter = counter
            print("SubscribeData: (Received Data from ECG) " + str(messageData) + " at time : " + str(current_time))
        # the data is inserted in the local file only when the measurement was collected from both sensors
        if self.iHealthData and self.EcgData:
            self.bothSensorDataReceived = True
            self.insertData()
        # if no data was collected in the last 30 seconds from any of the sensors then an alert is sent
        if self.EcgDataCounter > 3:
            msgBody = ("SubscribeData: *****----- In last 30 seconds, ARRIVES No data from ECG sensor ------***** " +
                       " at time : " + str(current_time))
            print msgBody
            teleWs.sendMsg("hospital", msgBody)

        if self.iHealthDataCounter > 3:
            msgBody = ("SubscribeData: *****----- In last 30 seconds, ARRIVES NO data from iHealth sensor -----***** " +
                       " at time : " + str(current_time))
            print msgBody
            teleWs.sendMsg("hospital", msgBody)
        return 'ok'

    @classmethod
    def insertData(self):
        ecgMsg = self.EcgData
        iHealthMsg = self.iHealthData
        get_time = datetime.datetime.now()
        current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open("localData.json", "r") as L:
                tmpLocalData = L.read()
                localData = json.loads(tmpLocalData)
            localDataJson = localData[ecgMsg['patientID']]
            # new data is added to the local file
            new_data = json.dumps({"HRwithIhealth": iHealthMsg['HR'],
                                   "BOwithIhealth": iHealthMsg['BO'],
                                   "iHealthMeasureTime": iHealthMsg['measurement_time'],
                                   "HRwithECG": ecgMsg['HR'],
                                   "EcgMeasureTime": ecgMsg['measurement_time'],
                                   "DateInsert": current_time,
                                   "ThingSpeak": 0,
                                   "ReadDataCount": 0})
            new_data_json = json.loads(new_data)
            # only the 15 most recent measurements are retained
            if len(localDataJson) < 16:
                localDataJson.append(new_data_json)
            else:
                localDataJson.pop(0)
                localDataJson.append(new_data_json)
            with open('localData.json', 'w') as outfile:
                json.dump(localData, outfile)

            self.iHealthData = ""
            self.EcgData = ""
            self.iHealthDataCounter = 0
            self.EcgDataCounter = 0

            print("SubscribeData: (successfully inserted to Local File) "
                  + str(new_data_json) + " at time : " + str(current_time))
        except KeyError:
            print("SubscribeData: (Error in updating the Local File)" + str(current_time))


class TelegramWS(object):
    def __init__(self, telegramUrl):
        self.telegramUrl = telegramUrl

    def sendMsg(self, group, msg):
        url = self.telegramUrl + "?group=" + group + "&msg=" + msg
        ok = requests.get(url)
        return ok.text


if '__main__' == __name__:
    with open("RcConfig.json", "r") as f:
        tmpConf = f.read()
        conf = json.loads(tmpConf)
        RcURL = conf["ResourseCatalogInfo"]["url"]
        telegramUrl = conf["telegram"]["sendMessageUrl"]
        if not str(RcURL).endswith('/'):
            RcURL = str(RcURL) + "/"

    client = mqtt.Client()
    teleWs = TelegramWS(telegramUrl)
    SubClass = SubscribeData(client, RcURL)

    while True:
        try:
            # get info related to the broker
            tmpBroker = requests.get(RcURL + "broker")
            brokerData = json.loads(tmpBroker.text)
            broker_ip = brokerData["Broker_IP"]
            broker_port = brokerData["Broker_port"]
            while True:
                try:
                    # specify the topics the subscriber is interested in
                    tmpTopics = requests.get(RcURL + "topic")
                    topics = json.loads(tmpTopics.text)
                    topic = topics["wildcards"]
                    while True:
                        try:
                            # establish a connection and subscribe for the topic
                            client.on_connect = SubClass.on_connect
                            client.on_subscribe = SubClass.on_subscribe
                            client.on_message = SubClass.on_message
                            ok = client.connect(broker_ip, int(broker_port))
                            client.subscribe(str(topic), qos=1)
                            client.loop_forever()
                            while True:
                                time.sleep(1)
                        except Exception:
                            msgBody = "SubscribeData: ERROR IN CONNECTING TO THE BROKER"
                            teleWs.sendMsg("developer", msgBody)
                            print msgBody
                        time.sleep(5)
                except Exception:
                    msgBody = "SubscribeData: There was an error in connecting to the Resource Catalog to get topics"
                    teleWs.sendMsg("developer", msgBody)
                    print msgBody
                time.sleep(5)
        except Exception:
            msgBody = "SubscribeData: There was an error in connecting to the Resource Catalog to get Broker Data"
            teleWs.sendMsg("developer", msgBody)
            print msgBody
