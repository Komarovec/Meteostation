import requests, json

#Trida pro posilani a zpracovavani HTTP requestu
class NetworkHandler:
    def __init__(self):
        global apiServer, apiKey;
        apiServer = "https://api.nag-iot.zcu.cz/"
        apiKey = "?api_key=MVXhOVCtx4nQSDjm" #Klic, pro jistotu, neni pritomny

    #Test pripojeni
    def testConnection(self):
        global apiServer, apiKey
        try:
            if(requests.get(apiServer+apiKey).status_code == 200):
                return "OK"
        except requests.exceptions.RequestException as e:
            print(e)
            return "No connection"
        
    #Zmeni hodnotu promenne
    def sendVar(self, name, value):
        global apiServer, apiKey
        url = apiServer+"v2/value/"+name+apiKey
        try:
            r = requests.post(url, json={"value": value})
            return r.status_code
        except requests.exceptions.RequestException as e:
            print(e)
            return 0
        
    #Precte promennou
    def readVar(self, name):
        global apiServer, apiKey
        url = apiServer+"v2/value/"+name+apiKey
        try:   
            r = requests.get(url)
            return r.content if r.status_code == 200 else False
        except requests.exceptions.RequestException as e:
            print(e)
            return False
