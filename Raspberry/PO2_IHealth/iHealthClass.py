import datetime
import json
import random
import time

import requests
from flask import request


class iHealth(object):
    def __init__(self):
        with open('iHealthConfig.json', 'r') as f:
            conf = json.load(f)

        if conf['ACCESS_TOKEN']:
            self.access_token = conf['ACCESS_TOKEN']
        else:
            self.access_token = ''

        if conf['REFRESH_TOKEN']:
            self.refresh_token = conf['REFRESH_TOKEN']
        else:
            self.refresh_token = ''

        if conf['USER_ID']:
            self.user_id = conf['USER_ID']
        else:
            self.user_id = ''

        # To get client_id and client_secret , you should register in site of https://developer.ihealthlabs.eu/
        # they give you these credentials
        self.client_id = conf['CLIENT_ID']
        self.client_secret = conf['CLIENT_SECRET']
        # the real redirect , because we want to use locally , we set http://localhost:5000/callback
        self.redirect_uri = conf['CALLBACK_URI']
        # on the registration form of iHealth you should give them a real callback url , but in our case we set a fake
        # url but it necessary to put in the parameter when you want connect to iHealth API
        self.redirect_uri_org = conf['CALLBACK_URI_org']
        # iHealth support OAuth version 1 and 2 , in this project we use second version and the url is :
        # https://oauthuser.ihealthlabs.eu/OpenApiV2/OAuthv2/userauthorization/
        self.auth_url = conf['AUTH_URL']
        # after the first step of authentication, we should use this link to connect for second Step
        self.auth_url_step2 = conf['AUTH_URL_step2']
        self.user_url = conf['USER_DATA_URL']
        # we get this parameter when we register on iHealth site
        self.user_data_sc =conf['DATA_TYPES_SC']
        self.user_data_sv =conf['DATA_TYPES_SV']
        self.response_type = 'code'  # default value for response_type
        self.APIName = 'OpenApiSpO2'  # it could be an array of target API , but in this project we just use OpenApiSpO2
        self.RequiredAPIName = 'OpenApiSpO2'
        self.IsNew = 'false'  # the system will be auto redirected to the sign up page

    def authorize(self):
        # if access token and user_id are not NULL it means authentication has done before
        if self.access_token and self.refresh_token and self.user_id:
            result = self.get_blood_oxygen(30)
            if result == "-2":
                payload = {'client_id': self.client_id,
                           'client_secret': self.client_secret,
                           'redirect_uri': self.redirect_uri_org,
                           'response_type': 'refresh_token',
                           'refresh_token': self.refresh_token}
                r = requests.get(self.auth_url_step2, params=payload,  cert='./idscertificate.pem')
                try:
                    self.access_token, self.refresh_token = self.get_tokens(r.text)
                    self.user_id = self.get_user_id(r.text)
                    self.saveData()
                    return "The token is refreshed"
                except:
                    print "there is an Error on conecting to iHealth server"
                return
            return 'No need to authentication, Just use the API'
        else:
            payload = {'client_id': self.client_id, 'response_type': self.response_type,
                       'redirect_uri': self.redirect_uri, 'APIName': self.APIName,
                       'RequiredAPIName': self.RequiredAPIName, 'IsNew': self.IsNew}
            r = requests.get(self.auth_url, params=payload)
            return r

    def callback(self):
        # we get a confirmation code from the first step of authentication
        code = self.get_code
        grant_type = 'authorization_code'  # is currently the only supported value
        payload = {'code': code, 'client_id': self.client_id, 'grant_type': grant_type,
                   'client_secret': self.client_secret, 'redirect_uri': self.redirect_uri_org}
        # except first step of Authentication , in all of connection to iHealth API we must you CERTIFICATE KEY
        r = requests.get(self.auth_url_step2, params=payload, cert='./idscertificate.pem')
        try:
            self.access_token, self.refresh_token = self.get_tokens(r.text)
            self.user_id = self.get_user_id(r.text)
            self.saveData()
            return r.text
        except:
            print "there is an Error on conecting to iHealth server"

    def saveData(self):
        with open('iHealthConfig.json', 'r') as f:
            config = json.load(f)

        config['ACCESS_TOKEN'] = self.access_token
        config['REFRESH_TOKEN'] = self.refresh_token
        config['USER_ID'] = self.user_id

        with open('iHealthConfig.json', 'w') as f:
            json.dump(config, f)

    def get_code(self):
        if 'code' not in request.args:
            return None
        return request.args['code']

    def get_tokens(self, data):
        resp = json.loads(data)
        if resp['AccessToken'] and resp['RefreshToken']:
            return resp['AccessToken'], resp['RefreshToken']
        else:
            return None, None  # this should be handled as an error

    def get_user_id(self, data):
        resp = json.loads(data)
        if resp['UserID']:
            return resp['UserID']
        else:
            return None

    def get_blood_oxygen(self, lastseconds):
        if self.access_token and self.user_id:
            base_url = self.user_url + str(self.user_id) + '/spo2.json/'
            payload = {'client_id': self.client_id, 'client_secret': self.client_secret,
                       'access_token': self.access_token, 'redirect_uri': self.redirect_uri_org,
                       'sc': self.user_data_sc, 'sv': self.user_data_sv}
            if lastseconds != 0:
                timeNow = int(time.time()) + 7200
                start_time = timeNow - lastseconds
                payload.update({'start_time': start_time})
            r = requests.get(base_url, params=payload, cert='./idscertificate.pem')
            datajson = json.loads(r.text)

            if "ErrorDescription" in datajson:
                if datajson["ErrorDescription"] == "Token is expired":
                    return "-2"
            else:
                Spo2Data = datajson['BODataList']
                if (len(Spo2Data) == 0):
                    with open('data.json', 'r') as f:
                        conf = json.load(f)
                    alldata = conf['BODataList']
                    randomId = random.randint(0, len(alldata))
                    lasdata = conf['BODataList'][randomId]
                    get_time = datetime.datetime.now()
                    current_time = get_time.strftime("%Y-%m-%d %H:%M:%S")
                    lasdata["measurement_time"] = current_time
                else:
                    Spo2DataLen = len(Spo2Data)
                    lasdata = Spo2Data[Spo2DataLen - 1]
                return lasdata
        else:
            return "-1"

