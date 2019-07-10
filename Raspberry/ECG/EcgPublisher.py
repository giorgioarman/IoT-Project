import datetime
import time
import paho.mqtt.client as mqtt
import json
import requests
import serial


class PublishEcgData(object):
    def __init__(self, client, rcURL, paitentID, telegramUrl):
        self.client = client
        self.rcURL = rcURL
        self.paitentID = paitentID
        self.telegramUrl = telegramUrl
        self.mustPublish = False
        self.lastPublishTime = ''
        self.msgSent = False
        self.lastMsgSent = ''

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

    def publish_ECG_data(self, HRdata):
        try:
            get_time = datetime.datetime.now()
            current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
            if HRdata:
                HR = HRdata
            new_data_json = json.dumps({"subject": "ECG", "patientID": self.paitentID,
                                        "HR": HR,
                                        "measurement_time": current_time})
            msg_info = client.publish(self.topic, new_data_json, qos=1)
            client.user_data_set(self.topic + " : " + new_data_json)
            if msg_info.is_published() == True:
                print ("PublishECG: Message is published.\n")
            msg_info.wait_for_publish()
            self.mustPublish = False
            self.lastPublishTime = time.time()
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

    def trigger(self):
        if not self.lastPublishTime:
            self.mustPublish = True
        else:
            if abs(self.lastPublishTime - time.time()) > 10:
                self.mustPublish = True
            else:
                self.mustPublish = False

        if self.msgSent:
            if abs(self.lastMsgSent - time.time()) > 60:
                self.msgSent = False


if __name__ == '__main__':

    with open("RcConfig.json", "r") as f:
        tmpConf = f.read()
        conf = json.loads(tmpConf)
        RcURL = conf["ResourseCatalogInfo"]["url"]
        if not str(RcURL).endswith('/'):
            RcURL = str(RcURL) + "/"
        paitentID = conf["ResourseCatalogInfo"]["PaitentID"]
        telegramUrl = conf["telegram"]["sendMessageUrl"]

        client = mqtt.Client('ECG')
        pubClass = PublishEcgData(client, RcURL, paitentID, telegramUrl)
        tmpBroker = requests.get(RcURL + "broker")
        brokerData = json.loads(tmpBroker.text)
        if brokerData:
            pubClass.get_topic()
            broker_ip = brokerData["Broker_IP"]
            broker_port = brokerData["Broker_port"]
            client.on_connect = PublishEcgData.on_connect
            client.on_publish = PublishEcgData.on_publish
            ok = client.connect(broker_ip, int(broker_port))
            client.loop_start()

            # create an object to Connect Arduino by USB
            serialPort = serial.Serial('COM5', 9600, timeout=.1)
            mustSendMsg = 0
            while True:
                if (serialPort.in_waiting > 0):
                    readLine = serialPort.readline()
                    if readLine:
                        dataSplitted = readLine.strip().split(" ")
                        HRData = dataSplitted[len(dataSplitted) - 1]
                        # control HeartBeat each time that collect from SENSOR

                        if int(HRData) < 45 or int(HRData) > 90:
                            mustSendMsg += 1
                            if mustSendMsg > 1 and not pubClass.msgSent:
                                msg = paitentID + " is critical with Heart Rate: %s bpm" % HRData
                                result = pubClass.sendMsg("hospital", msg)
                                pubClass.msgSent = True
                                pubClass.lastMsgSent = time.time()
                                mustSendMsg = 0
                            else:
                                mustSendMsg = 0
                        else:
                            mustSendMsg = 0

                        print(HRData)
                        pubClass.trigger()
                        if pubClass.mustPublish:
                            pubClass.publish_ECG_data(HRData)
                        time.sleep(0.5)

    #
    # while True:
    #     try:
    #         with open("RcConfig.json", "r") as f:
    #             tmpConf = f.read()
    #             conf = json.loads(tmpConf)
    #             RcURL = conf["ResourseCatalogInfo"]["url"]
    #             if not str(RcURL).endswith('/'):
    #                 RcURL = str(RcURL) + "/"
    #             paitentID = conf["ResourseCatalogInfo"]["PaitentID"]
    #             telegramUrl = conf["telegram"]["sendMessageUrl"]
    #         while True:
    #             try:
    #                 client = mqtt.Client('ECG')
    #                 pubClass = PublishEcgData(client, RcURL, paitentID, telegramUrl)
    #                 tmpBroker = requests.get(RcURL + "broker")
    #                 brokerData = json.loads(tmpBroker.text)
    #                 if brokerData:
    #                     pubClass.get_topic()
    #                     try:
    #                         broker_ip = brokerData["Broker_IP"]
    #                         broker_port = brokerData["Broker_port"]
    #                         client.on_connect = PublishEcgData.on_connect
    #                         client.on_publish = PublishEcgData.on_publish
    #                         ok = client.connect(broker_ip, int(broker_port))
    #                         client.loop_start()
    #
    #                         #create an object to Connect Arduino by USB
    #                         serialPort = serial.Serial('COM5', 9600, timeout=.1)
    #                         mustSendMsg = 0
    #
    #                         while True:
    #                             if (serialPort.in_waiting > 0):
    #                                 readLine = serialPort.readline()
    #                                 if readLine:
    #                                     dataSplitted = readLine.strip().split(" ")
    #                                     HRData = dataSplitted[len(dataSplitted) - 1]
    #                                     # control HeartBeat each time that collect from SENSOR
    #
    #                                     if HRData < 45 or HRData > 90:
    #                                         mustSendMsg += 1
    #                                         if mustSendMsg > 1:
    #                                             msg = "%s is critical with Heart Rate: %s bpm" %paitentID, HRData
    #                                             result = pubClass.sendMsg("hospital", msg)
    #                                             pubClass.msgSent = True
    #                                             pubClass.lastMsgSent = time.time()
    #                                             mustSendMsg = 0
    #
    #                                     print(HRData)
    #                                     pubClass.trigger()
    #                                     if pubClass.mustPublish:
    #                                         pubClass.publish_ECG_data(HRData)
    #
    #                     except Exception:
    #                         msgBody = "PublishECG: ERROR IN CONNECTING TO THE BROKER"
    #                         print msgBody
    #                         pubClass.sendMsg("developer", msgBody)
    #             except Exception:
    #                 msgBody = "PublishECG: There is an error with connecting to Resource Catalog"
    #                 print msgBody
    #                 pubClass.sendMsg("developer", msgBody)
    #             time.sleep(10)
    #     except Exception:
    #         msgBody = "PublishECG: ERROR IN OPENING RcConfig.Json File"
    #         print msgBody
    #     time.sleep(5)