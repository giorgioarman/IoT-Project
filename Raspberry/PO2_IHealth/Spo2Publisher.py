import datetime
import time
import paho.mqtt.client as mqtt
import json
import requests
from iHealthClass import iHealth


class PublishSpo2Data(object):
    def __init__(self, spo2Class, client, rcURL, paitentID):
        self.spo2Class = spo2Class
        self.client = client
        self.rcURL = rcURL
        self.paitentID = paitentID

    @staticmethod
    def on_connect(client, userdata, flags, rc):
        get_time = datetime.datetime.now()
        current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
        print ('PublishSpo2: Connecting to Broker has done successfully at time: ' + str(current_time))
        return str(rc)

    @classmethod
    def on_publish(cls, client, userdata, mid):
        get_time = datetime.datetime.now()
        current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
        print("PublishSpo2:(successfully) " + str(userdata) + " at time : " + str(current_time))
        return str(mid)

    def publish_Spo2_data(self):
        try:
            data = self.spo2Class.get_blood_oxygen(30)
            BO = data["BO"]
            HR = data["HR"]
            measurement_time = data["measurement_time"]
            new_data_json = json.dumps({"subject": "spo2",
                                        "patientID": self.paitentID,
                                        "BO": BO,
                                        "HR": HR,
                                        "measurement_time": measurement_time})
            msg_info = client.publish(self.topic, new_data_json, qos=1)
            client.user_data_set(self.topic + " : " + new_data_json)
            if msg_info.is_published() == True:
                print ("PublishSpo2: Message is published.\n")
            msg_info.wait_for_publish()
            return "maybe is ok"
        except:
            get_time = datetime.datetime.now()
            current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
            print ("PublishSpo2: ERROR IN PUBLISHING " + "at time: " + str(current_time))

    def get_topic(self):
        try:
            tmpTopic = requests.get(self.rcURL + str(self.paitentID))
            topics = json.loads(tmpTopic.text)["Topics"]
            self.topic = topics["Spo2"]
        except:
            print "PublishSpo2: There is am error with connecting to Resource Catalog"


if __name__ == '__main__':
    with open("RcConfig.json", "r") as f:
        tmpConf = f.read()
        conf = json.loads(tmpConf)
        RcURL = conf["ResourseCatalogInfo"]["url"]
        if not str(RcURL).endswith('/'):
            RcURL = str(RcURL) + "/"
        paitentID = conf["ResourseCatalogInfo"]["PaitentID"]

    try:
        Spo2Class = iHealth()
    except:
        print "PublishSpo2: ERROR IN GETTING DATA FROM iHealth"

    client = mqtt.Client('SPO2')
    pubClass = PublishSpo2Data(Spo2Class, client, RcURL, paitentID)

    while True:
        try:
            tmpBroker = requests.get(RcURL + "broker")
            brokerData = json.loads(tmpBroker.text)
        except:
            print "PublishSpo2: There is am error with connecting to Resource Catalog"

        pubClass.get_topic()

        broker_ip = brokerData["Broker_IP"]
        broker_port = brokerData["Broker_port"]

        try:
            client.on_connect = PublishSpo2Data.on_connect
            client.on_publish = PublishSpo2Data.on_publish
            ok = client.connect(broker_ip, int(broker_port))
            client.loop_start()
        except:
            print "PublishSpo2: ERROR IN CONNECTING TO THE BROKER"
        while True:
            pubClass.publish_Spo2_data()
            time.sleep(10)