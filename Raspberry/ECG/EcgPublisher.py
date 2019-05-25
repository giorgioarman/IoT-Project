import datetime
import time
import paho.mqtt.client as mqtt
import json
import requests


class PublishEcgData(object):
    def __init__(self, client, rcURL, paitentID):
        self.client = client
        self.rcURL = rcURL
        self.paitentID = paitentID

    @staticmethod
    def on_connect(client, userdata, flags, rc):
        get_time = datetime.datetime.now()
        current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
        print ('PublishECG: Connecting to Broker has done successfully at time: ' + str(current_time))
        return str(rc)

    @classmethod
    def on_publish(cls, client, userdata, mid):
        get_time = datetime.datetime.now()
        current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
        print("PublishECG:(successfully) " + str(userdata) + " at time : " + str(current_time))
        return str(mid)

    def publish_ECG_data(self):
        try:
            get_time = datetime.datetime.now()
            current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
            HR = 90
            new_data_json = json.dumps({"subject": "ECG", "patientID": self.paitentID,
                                        "HR": HR,
                                        "measurement_time": current_time})
            msg_info = client.publish(self.topic, new_data_json, qos=1)
            client.user_data_set(self.topic + " : " + new_data_json)
            if msg_info.is_published() == True:
                print ("PublishECG: Message is published.\n")
            msg_info.wait_for_publish()
            return "maybe is ok"
        except:
            get_time = datetime.datetime.now()
            current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
            print ("PublishECG: ERROR IN PUBLISHING " + "at time: " + str(current_time))

    def get_topic(self):
        try:
            tmpTopic = requests.get(self.rcURL + str(self.paitentID))
            topics = json.loads(tmpTopic.text)["Topics"]
            self.topic = topics["ECG"]
        except:
            print "PublishECG: There is am error with connecting to Resource Catalog"


if __name__ == '__main__':
    with open("RcConfig.json", "r") as f:
        tmpConf = f.read()
        conf = json.loads(tmpConf)
        RcURL = conf["ResourseCatalogInfo"]["url"]
        if not str(RcURL).endswith('/'):
            RcURL = str(RcURL) + "/"
        paitentID = conf["ResourseCatalogInfo"]["PaitentID"]

    client = mqtt.Client('ECG')
    pubClass = PublishEcgData(client, RcURL, paitentID)

    while True:
        try:
            tmpBroker = requests.get(RcURL + "broker")
            brokerData = json.loads(tmpBroker.text)
        except:
            print "PublishECG: There is am error with connecting to Resource Catalog"

        pubClass.get_topic()

        broker_ip = brokerData["Broker_IP"]
        broker_port = brokerData["Broker_port"]

        try:
            client.on_connect = PublishEcgData.on_connect
            client.on_publish = PublishEcgData.on_publish
            ok = client.connect(broker_ip, int(broker_port))
            client.loop_start()
        except:
            print "PublishECG: ERROR IN CONNECTING TO THE BROKER"
        while True:
            pubClass.publish_ECG_data()
            time.sleep(10)