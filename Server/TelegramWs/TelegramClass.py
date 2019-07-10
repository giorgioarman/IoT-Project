import telepot


class TelegramClass(object):
    def __init__(self, token):
        self.token = token
        self.telebot = telepot.Bot(self.token)
        self.isConnected = False
        self.lastUpdateid = 391598136

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

    def getUpdate(self):
        if self.isConnected:
            dataFromTelegram = self.telebot.getUpdates(self.lastUpdateid)
            return dataFromTelegram

    def sendMsg(self, chatId, Msg, reply_markup=None):
        if self.isConnected:
            try:
                self.telebot.sendMessage(chatId, Msg, reply_markup=reply_markup)
                return True
            except ValueError:
                return False
        else:
            return "Need to connect to Telegram server"