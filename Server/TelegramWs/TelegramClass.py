import telepot
import time
import json


class TelegramClass(object):
    def __init__(self, token):
        self.token = token
        self.telebot = telepot.Bot(self.token)
        self.isConnected = False
        self.lastUpdateid = 257031516

    def connectToTelegram(self):
        try:
            result = self.telebot.getMe()
            if result['is_bot']:
                print('successfully connect to BOT \nUser Name : ' + result['username'])
                self.isConnected = True
                return True
        except:
            print("Error in Conecction")
            return False

    def getUpdateFromTelegram(self):
        if self.isConnected:
            dataFromTelegram = self.telebot.getUpdates(self.lastUpdateid)
            for x in range(len(dataFromTelegram) - 1):
                    textMSG = ''
                    userName = ''
                    try:
                        textMSG = dataFromTelegram[x+1]['message']['text']
                        userName = dataFromTelegram[x+1]['message']['from']['first_name']
                    except:
                        print "there is no text on the msg"

                    if textMSG or textMSG.strip():
                        print "I recived your message : \n ", textMSG
                        self.lastUpdateid = dataFromTelegram[x+1]['update_id']
                        if userName or userName.strip():
                            self.telebot.sendMessage("-1001073430063", "hey " + userName + "\nI received your message  \n" + textMSG)
                        else:
                            self.telebot.sendMessage("-1001073430063", "I received your message  \n" + textMSG)
                    else:
                        self.telebot.sendMessage("-1001073430063", "It's not a defined command")
                        self.lastUpdateid = dataFromTelegram[x + 1]['update_id']

    def sendMsg(self, chatId, Msg):
        if self.isConnected:
            try:
                self.telebot.sendMessage(chatId, Msg)
                return True
            except ValueError:
                return False
        else:
            return "Need to connect to Telegram server"


# if __name__ == '__main__':
#     bot = TelegramClass("657264767:AAFnhyN_3Ku8EOxv5rUlbxEWiiDHj75ddlQ")
#     bot.connectToTelegram()
#
#     while True:
#         bot.getUpdateFromTelegram()
#         time.sleep(1)


# print ss
#
# bot = telegramBot("657264767:AAFnhyN_3Ku8EOxv5rUlbxEWiiDHj75ddlQ")
# # bot = telepot.Bot("657264767:AAFnhyN_3Ku8EOxv5rUlbxEWiiDHj75ddlQ")
#
# lastUpdateid = 257031516
# while True:
#     dataFromTelegram = bot.getUpdates(lastUpdateid)
#     if len(dataFromTelegram) > 1:
#         for x in range(len(dataFromTelegram) - 1):
#             textMSG = ''
#             userName =''
#             try:
#                 textMSG = dataFromTelegram[x+1]['message']['text']
#                 userName = dataFromTelegram[x+1]['message']['from']['first_name']
#             except:
#                 print "there is no text on the msg"
#
#             if textMSG or textMSG.strip():
#                 print "I recived your message : \n ", textMSG
#                 lastUpdateid = dataFromTelegram[x+1]['update_id']
#                 if userName or userName.strip():
#                     bot.sendMessage("-1001073430063", "hey " + userName + "\nI received your message  \n" + textMSG)
#                 else:
#                     bot.sendMessage("-1001073430063", "I received your message  \n" + textMSG)
#             else:
#                 bot.sendMessage("-1001073430063", "It's not a defined command")
#                 lastUpdateid = dataFromTelegram[x + 1]['update_id']
#
#     time.sleep(1)
#
#
#





