import cherrypy
import json
from TelegramClass import TelegramClass


class TelegramWebService(object):
    def __init__(self, teleToken, developerChatId, hospitalChatId):
        self.teleClass = TelegramClass(teleToken)
        self.developerChatId = developerChatId
        self.hospitalChatId = hospitalChatId
        self.isConnected = self.teleClass.connectToTelegram()


    exposed = True

    def GET(self, *uri, **params):
        if self.isConnected:
            if len(uri) == 0:
                return "you have not entered the command"
            else:
                RequestCommand = str(uri[0]).lower()
                if RequestCommand == "sendmessage":
                    if len(params) < 2:
                        return "you have not entered right parameters, use like this command:  \n" + \
                               " localhost:8091\\sendmessage?group=hospital&msg=test"
                    else:
                        chatid = ""
                        msg = ""
                        for item in params:
                            if item.lower() == "group":
                                if params[item].lower() == "hospital":
                                    chatid = self.hospitalChatId
                                elif params[item].lower() == "developer":
                                    chatid = self.developerChatId
                                else:
                                    return "The group is NOT valid."
                            elif item.lower() == "msg":
                                msg = params[item]

                        if not chatid:
                            return "chatId is not inserted"
                        if not msg:
                            return "msg is not inserted"

                        if msg and chatid:
                            try:
                                self.teleClass.sendMsg(chatid, msg)
                                return "The msg has been sent"
                            except Exception:
                                return "There was an error to send msg "


        else:
            return "The webservice is not connected to Telegram"


if '__main__' == __name__:

    with open("TelegramConfig.json", "r") as f:
        tmpConf = f.read()
        TelegramConfig = json.loads(tmpConf)

    WsIp = TelegramConfig["TelegramInfo"]["ip"]
    WsPort = TelegramConfig["TelegramInfo"]["port"]
    telegramToken = TelegramConfig["TelegramInfo"]["token"]
    developerChatId = TelegramConfig["TelegramInfo"]["developerChatId"]
    hostpitalChatId = TelegramConfig["TelegramInfo"]["hostpitalChatId"]
    # tClass = TelegramWebService(telegramToken)
    # tClass.connectToTelegram()

    confCherry = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }

    cherrypy.tree.mount(TelegramWebService(telegramToken, developerChatId, hostpitalChatId), '/', confCherry)
    cherrypy.config.update({
        "server.socket_host": str(WsIp),
        "server.socket_port": int(WsPort),
    })
    cherrypy.engine.start()
    cherrypy.engine.block()

