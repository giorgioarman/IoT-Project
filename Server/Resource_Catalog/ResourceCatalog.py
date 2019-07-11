import cherrypy
import json

# Definizione della classe 'ResourceCatalog'
class ResourceCatalog(object): 
    exposed = True
    # Definzione funzione GET
    def GET(self, *uri, **param):
        with open("RcData.json", "r") as t: 
            tmpData = t.read()
            RcDataJson = json.loads(tmpData)

        if len(uri) == 0:
            return "you have not entered the command"
        else:
            RequestCommand = str(uri[0]).lower()
            if RequestCommand in RcDataJson:
                res = RcDataJson[RequestCommand]
                reqData = json.dumps(res)
                return reqData


if '__main__' == __name__:

    with open("RcConfig.json", "r") as f:
        tmpConf = f.read()
        ResourceCatalogConfig = json.loads(tmpConf)

    RcIp = ResourceCatalogConfig["ResourseCatalogInfo"]["ip"]
    RcPort = ResourceCatalogConfig["ResourseCatalogInfo"]["port"]

    confCherry = {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.sessions.on': True,
        }
    }

    cherrypy.tree.mount(ResourceCatalog(), '/', confCherry)
    cherrypy.config.update({
        "server.socket_host": str(RcIp),
        "server.socket_port": int(RcPort),
    })
    cherrypy.engine.start()
    cherrypy.engine.block()

