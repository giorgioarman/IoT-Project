import requests

from TelegramClass import TelegramClass
import time
from telepot.namedtuple import ReplyKeyboardMarkup, KeyboardButton
import json


class TelegramService(object):
    def __init__(self, teleToken, restApiUrl):
        self.teleClass = TelegramClass(teleToken)
        self.isConnected = self.teleClass.connectToTelegram()
        self.restApiUrl = restApiUrl

    def reconecting(self):
        self.isConnected = self.teleClass.connectToTelegram()

    def handleRecivedMsg(self):
        recivedMsg = self.teleClass.getUpdate()
        for x in range(len(recivedMsg) - 1):
            textMSG = ''
            userName = ''
            try:
                textMSG = recivedMsg[x + 1]['message']['text']
                userName = recivedMsg[x + 1]['message']['from']['first_name']
            except Exception:
                self.teleClass.lastUpdateid = recivedMsg[x + 1]['update_id']
                print "there is no text on the msg"
            requestUrl = "http://" + self.restApiUrl + "getalldata/" + textMSG
            tmpPatientData = requests.get(requestUrl)
            try:
                patientData = json.loads(tmpPatientData.text)
                lastData = patientData[-6:]
                bodyMessage = ''
                for item in lastData:
                    HRwithIhealth = item["HRwithIhealth"]
                    BOwithIhealth = item["BOwithIhealth"]
                    HRwithECG = item["HRwithECG"]
                    dataMeasure = item["DateInsert"]
                    bodyMessage += "HR with ECG : " + str(HRwithECG) + "\n" +\
                                   "SpO2 with iHealth : " + str(BOwithIhealth) + "\n" +\
                                   "Time : " + str(dataMeasure) + "\n" +\
                                   "------------" + "\n"
                self.teleClass.sendMsg("-1001073430063",
                                       bodyMessage)
                print textMSG + ":" + bodyMessage
                self.teleClass.lastUpdateid = recivedMsg[x + 1]['update_id']
            except:
                tmpPatientData = requests.get("http://" + self.restApiUrl + "getallpatientid")

                patientData = json.loads(tmpPatientData.text)

                # patientData = [1,2,3,4,3,5,3,4]

                listOfKeyboard = []
                for i in patientData:
                    listOfKeyboard.append(KeyboardButton(text=i))

                multiKeyboard = [listOfKeyboard[x:x + 2] for x in range(0, len(listOfKeyboard), 2)]
                replyKeyboard = ReplyKeyboardMarkup(keyboard= multiKeyboard,resize_keyboard=True)
                self.teleClass.sendMsg(chatId="-1001073430063",
                                       Msg="hey " + userName + "\nI received your message  \n" + textMSG,
                                       reply_markup=replyKeyboard)
                self.teleClass.lastUpdateid = recivedMsg[x + 1]['update_id']


if __name__ == '__main__':
    with open("RcConfig.json", "r") as f:
        tmpConf = f.read()
        conf = json.loads(tmpConf)
        RcURL = conf["ResourseCatalogInfo"]["url"]
        Token = conf["telegram"]["token"]
        if not str(RcURL).endswith('/'):
            RcURL = str(RcURL) + "/"

    tmpApi = requests.get(RcURL + "restapi")
    apiRestConf = json.loads(tmpApi.text)
    restApiIp = apiRestConf["ip"]
    restApiPort = apiRestConf["port"]
    restApiURL = restApiIp + ":" + restApiPort + "/"


    bot = TelegramService(Token,restApiURL)

    while True:
        if bot.isConnected:
            handleLoop = True
            print 'successfully connected to Telegram'
            while handleLoop:
                try:
                    bot.handleRecivedMsg()
                    time.sleep(1)
                except Exception:
                    print 'error during loop for Handle receiving Data'
                    bot.isConnected = False
                    handleLoop = False
        else:
            time.sleep(3)
            bot.reconecting()