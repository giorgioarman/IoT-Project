import cherrypy
import json

import requests
from flask import request


class RestAPIClass(object):
    exposed = True

    def GET(self, *uri, **param):
        urlLen = len(uri)
        if len(uri) == 0:
            return "you have not entered the command"
        else:
            RequestCommand = str(uri[0]).lower()
            if RequestCommand == 'getalldata':
                try:
                    patientId = uri[1]
                    with open("localData.json", "r") as L:
                        tmpLocalData = L.read()
                        localData = json.loads(tmpLocalData)
                        try:
                            localDataJson = localData[patientId]
                            return json.dumps(localDataJson)
                        except:
                            return 'There is no Data or patient id is not valid'
                except:
                    return 'you have not entered the patient ID'
            elif RequestCommand == 'getallpatientid':
                try:
                    with open("localData.json", "r") as L:
                        tmpLocalData = L.read()
                        localData = json.loads(tmpLocalData)
                        try:
                            localDataJson = localData.keys()
                            return json.dumps(localDataJson)
                        except:
                            return 'There is no Data or patient id is not valid'
                except:
                    return 'you have not entered the patient ID'


if '__main__' == __name__:

    with open("RcConfig.json", "r") as f:
        tmpConf = f.read()
        conf = json.loads(tmpConf)
        telegramUrl = conf["telegram"]["sendMessageUrl"]
        RcURL = conf["ResourseCatalogInfo"]["url"]
        if not str(RcURL).endswith('/'):
            RcURL = str(RcURL) + "/"

    tmpApi = requests.get(RcURL + "restapi")
    apiRestConf = json.loads(tmpApi.text)
    restApiIp = apiRestConf["ip"]
    restApiPort = apiRestConf["port"]
    confCherry = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }

    cherrypy.tree.mount(RestAPIClass(), '/', confCherry)
    cherrypy.config.update({
        "server.socket_host": str(restApiIp),
        "server.socket_port": int(restApiPort),
    })
    cherrypy.engine.start()
    cherrypy.engine.block()

