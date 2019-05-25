import datetime
import time
import paho.mqtt.client as mqtt
import json
import requests


class PublishEcgData(object):
    def __init__(self, client, rcURL, paitentID, telegramUrl):
        self.client = client
        self.rcURL = rcURL
        self.paitentID = paitentID
        self.telegramUrl = telegramUrl

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
        except Exception:
            get_time = datetime.datetime.now()
            current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
            msgBody = ("PublishECG: ERROR IN PUBLISHING " + "at time: " + str(current_time))
            print msgBody
            self.sendMsg("developer", msgBody)

    def get_topic(self):
        try:
            tmpTopic = requests.get(self.rcURL + str(self.paitentID))
            topics = json.loads(tmpTopic.text)["Topics"]
            self.topic = topics["ECG"]
        except Exception:
            msgBody = "PublishECG: There is am error with connecting to Resource Catalog"
            print msgBody
            self.sendMsg("developer", msgBody)

    def sendMsg(self, group, msg):
        try:
            url = self.telegramUrl + "?group=" + group + "&msg=" + msg
            ok = requests.get(url)
            return ok.text
        except Exception:
            print "There is an error for sending msg"


if __name__ == '__main__':
    while True:
        try:
            with open("RcConfig.json", "r") as f:
                tmpConf = f.read()
                conf = json.loads(tmpConf)
                RcURL = conf["ResourseCatalogInfo"]["url"]
                if not str(RcURL).endswith('/'):
                    RcURL = str(RcURL) + "/"
                paitentID = conf["ResourseCatalogInfo"]["PaitentID"]
                telegramUrl = conf["telegram"]["sendMessageUrl"]
            while True:
                try:
                    client = mqtt.Client('ECG')
                    pubClass = PublishEcgData(client, RcURL, paitentID, telegramUrl)
                    tmpBroker = requests.get(RcURL + "broker")
                    brokerData = json.loads(tmpBroker.text)
                    if brokerData:
                        pubClass.get_topic()
                        try:
                            broker_ip = brokerData["Broker_IP"]
                            broker_port = brokerData["Broker_port"]
                            client.on_connect = PublishEcgData.on_connect
                            client.on_publish = PublishEcgData.on_publish
                            ok = client.connect(broker_ip, int(broker_port))
                            client.loop_start()
                            while True:
                                pubClass.publish_ECG_data()
                                time.sleep(10)
                        except Exception:
                            msgBody = "PublishECG: ERROR IN CONNECTING TO THE BROKER"
                            print msgBody
                            pubClass.sendMsg("developer", msgBody)
                except Exception:
                    msgBody = "PublishECG: There is an error with connecting to Resource Catalog"
                    print msgBody
                    pubClass.sendMsg("developer", msgBody)
                time.sleep(10)
        except Exception:
            msgBody = "PublishECG: ERROR IN OPENING RcConfig.Json File"
            print msgBody
        time.sleep(5)