import requests
import xmltodict
from pyrate_limiter import RequestRate, Duration, Limiter
from requests_ntlm import HttpNtlmAuth


def get_ids(xml_dic, keys):
    res = xml_dic
    for k in keys:
        res = res.get(k, {})
    return res


def get_header(param):
    return {"Accept-Encoding": "gzip,deflate", "Content-Type": "text/xml;charset=UTF-8",
            "SOAPAction": "http://tempuri.org/" + param}


class Loader:
    def __init__(self, url: str, user: str = "", password: str = "", domain: str = ""):
        self.__url = url
        self.__user = user
        self.__pass = password
        self.__domain = domain
        rate = RequestRate(10, Duration.SECOND)
        self.limiter = Limiter(rate)

    def get_list(self, ):
        self.rate_limit()
        reqxml = '''<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:tem="http://tempuri.org/">
   <soap:Header/>
   <soap:Body>
      <tem:GetList>
         <tem:ts></tem:ts>
         <tem:teismas>00000013-e5a4-4275-b71d-40a1ab5dfb22</tem:teismas>
         <!-- <tem:teismoRumai></tem:teismoRumai> -->
      </tem:GetList>
   </soap:Body>
</soap:Envelope>
'''
        r = requests.post(self.__url, auth=self.get_auth(), data=reqxml,
                          timeout=30, headers=get_header("GetList"))
        if r.status_code != 200:
            raise Exception("Can't get list '{}'".format(r.text))
        xml_dic = xmltodict.parse(r.text)
        res = get_ids(xml_dic, ["soap:Envelope", "soap:Body", "GetListResponse", "GetListResult", "TpDocList", "guid"])

        return res

    def rate_limit(self):
        self.limiter.ratelimit("request", delay=True, max_delay=Duration.SECOND * 60)

    def get_one(self, file):
        self.rate_limit()
        reqxml = '''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header/>
   <soapenv:Body>
      <tem:GetOneDocument>
         <tem:id>%s</tem:id>
      </tem:GetOneDocument>
   </soapenv:Body>
</soapenv:Envelope>
        ''' % file
        r = requests.post(self.__url, auth=self.get_auth(), data=reqxml,
                          timeout=30, headers=get_header("GetOneDocument"))
        if r.status_code != 200:
            raise Exception("Can't get doc '{}'".format(r.text))
        return r.text

    def get_auth(self):
        return HttpNtlmAuth(self.__domain + '\\' + self.__user, self.__pass)
