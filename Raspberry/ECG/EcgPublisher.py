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
        self.mustPublish = False # initialization to false for the publishing of the data. After 10s of the last pubblication, it becomes TRUE
        self.lastPublishTime = '' # empty inizialization of the last publishing time. When a publication is performed, it containts the time of the last publication
        self.msgSent = False # initialization to false of the sent message. In the code it will become TRUE when the message is sent
        self.lastMsgSent = '' # empty inizialization of the time of the last sent message. So it provides the time when a message is sent

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
                                        "measurement_time": current_time}) #Publication of ECG-PatientID, HR value and time
            msg_info = client.publish(self.topic, new_data_json, qos=1)
            client.user_data_set(self.topic + " : " + new_data_json)
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
            if abs(self.lastPublishTime - time.time()) > 10: #in order to avoid too many publications, a pubblication can be performed only if more than 10 s are passed
                self.mustPublish = True # the publication must be performed
            else:
                self.mustPublish = False # the publication must not be performed

        if self.msgSent:
            if abs(self.lastMsgSent - time.time()) > 60: # in order to avoid too many messages sent, more than 60 s must pass before sending a new message
                self.msgSent = False # after 60 s after a message is sent (msgSent is TRUE in this interval), we have to inizializa again mgsSent to FALSE


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
            serialPort = serial.Serial('/dev/ttyACM0', 9600, timeout=.1) # acquisition from Arduino through USB port
            mustSendMsg = 0 # counter inizialization
            while True:
                pubClass.trigger()
                readLine = serialPort.readline()
                if readLine:
                    dataSplitted = readLine.strip().split(" ")
                    HRData = dataSplitted[len(dataSplitted) - 1]
                    
                    # Heart beat values control

                    if int(HRData) < 45 or int(HRData) > 90: #  HR values threshold for bed ridden patients
                        mustSendMsg += 1 # increase of the counter if the HR value is out of the threshold
                        if mustSendMsg > 1 and not pubClass.msgSent: # if there are more than one consecutive values out of the range and a message has not been sent yet
                            msg = paitentID + " is critical with Heart Rate: %s bpm" % HRData
                            print msg
                            result = pubClass.sendMsg("hospital", msg) #message sent in the hospital group
                            pubClass.msgSent = True # a message has been sent
                            pubClass.lastMsgSent = time.time() # time at which a message has been sent
                            mustSendMsg = 0
                    else:
                        mustSendMsg = 0

                    print(HRData)
                   
                    if pubClass.mustPublish: 
                        pubClass.publish_ECG_data(HRData) # publish the data after 10 s
