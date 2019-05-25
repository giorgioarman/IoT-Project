import datetime
import time
import paho.mqtt.client as mqtt
import json
import requests
from SendToThingSpeak import ThingSpeak


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

        if self.iHealthData and self.EcgData:
            self.bothSensorDataReceived = True
            self.insertData()

        if self.EcgDataCounter > 3:
            print("SubscribeData: ******------ In last 30 seconds, ARRIVES No data from ECG sensor -------****** "
                  + " at time : " + str(current_time))

        if self.iHealthDataCounter > 3:
            print("SubscribeData: ******------ In last 30 seconds, ARRIVES NO data from iHealth sensor ------****** " +
                  " at time : " + str(
                    current_time))
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
            new_data = json.dumps({"HRwithIhealth": iHealthMsg['HR'],
                                   "BOwithIhealth": iHealthMsg['BO'],
                                   "iHealthMeasureTime": iHealthMsg['measurement_time'],
                                   "HRwithECG": ecgMsg['HR'],
                                   "EcgMeasureTime": ecgMsg['measurement_time'],
                                   "DateInsert": current_time,
                                   "ThingSpeak": 0,
                                   "ReadDataCount": 0})
            new_data_json = json.loads(new_data)
            if len(localDataJson) < 11:
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
            print("SubscribeData: (Error in inserted to Local File)" + str(current_time))


if '__main__' == __name__:

    with open("RcConfig.json", "r") as f:
        tmpConf = f.read()
        conf = json.loads(tmpConf)
        RcURL = conf["ResourseCatalogInfo"]["url"]
        if not str(RcURL).endswith('/'):
            RcURL = str(RcURL) + "/"

    client = mqtt.Client()
    SubClass = SubscribeData(client, RcURL)

    while True:
        try:
            tmpBroker = requests.get(RcURL + "broker")
            brokerData = json.loads(tmpBroker.text)
        except:
            print "SubscribeData: There is am error with connecting to Resource Catalog"

        broker_ip = brokerData["Broker_IP"]
        broker_port = brokerData["Broker_port"]

        try:
            tmpTopics = requests.get(RcURL + "topic")
            topics = json.loads(tmpTopics.text)
        except:
            print "SubscribeData: There is am error with connecting to Resource Catalog"

        topic = topics["wildcards"]

        try:
            client.on_connect = SubClass.on_connect
            client.on_subscribe = SubClass.on_subscribe
            client.on_message = SubClass.on_message
            ok = client.connect(broker_ip, int(broker_port))
            client.subscribe(str(topic), qos=1)
            client.loop_forever()
        except:
            print "PublishSpo2: ERROR IN CONNECTING TO THE BROKER"
        while True:
            # pubClass.publish_Spo2_data()
            time.sleep(1)


