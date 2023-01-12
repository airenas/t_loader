import requests
import xmltodict
from pyrate_limiter import RequestRate, Duration, Limiter
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests_ntlm import HttpNtlmAuth


def get_ids(xml_dic, keys):
    res = xml_dic
    for k in keys:
        res = res.get(k, {})
    return res


def get_header(param):
    return {"Accept-Encoding": "gzip,deflate", "Content-Type": "text/xml;charset=UTF-8",
            "SOAPAction": "http://tempuri.org/" + param}


def default_limiter():
    rate = RequestRate(10, Duration.SECOND)
    return Limiter(rate)


class Cfg:
    def __init__(self, url: str, limiter: Limiter = default_limiter(), user: str = "", password: str = "",
                 domain: str = ""):
        self.url = url
        self.user = user
        self.password = password
        self.domain = domain
        self.limiter = limiter

    def get_auth(self):
        return HttpNtlmAuth(self.domain + '\\' + self.user, self.password)

    def rate_limit(self, resp, *args, **kwargs):
        self.limiter.ratelimit("request", delay=True, max_delay=Duration.SECOND * 60)


def init_client(cfg: Cfg):
    retry_strategy = Retry(total=2, backoff_factor=1.5, status_forcelist=[404, 429, 500, 502, 503, 504],
                           method_whitelist=["POST"])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http_client = requests.Session()
    http_client.mount("https://", adapter)
    http_client.mount("http://", adapter)
    http_client.hooks['response'].append(cfg.rate_limit)
    return http_client


class Loader:
    def __init__(self, cfg: Cfg):
        self.__cfg = cfg
        self.__http_client = init_client(self.__cfg)

    def get_list(self, court):
        reqxml = '''<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:tem="http://tempuri.org/">
   <soap:Header/>
   <soap:Body>
      <tem:GetList>
         <tem:ts></tem:ts>
         <tem:teismas>%s</tem:teismas>
         <!-- <tem:teismoRumai></tem:teismoRumai> -->
      </tem:GetList>
   </soap:Body>
</soap:Envelope>
''' % court
        r = self.__http_client.post(self.__cfg.url, auth=self.__cfg.get_auth(), data=reqxml,
                                    timeout=30, headers=get_header("GetList"))
        r.raise_for_status()
        xml_dic = xmltodict.parse(r.text)
        res = get_ids(xml_dic, ["soap:Envelope", "soap:Body", "GetListResponse", "GetListResult", "TpDocList", "guid"])

        return res

    def get_one(self, file):
        reqxml = '''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tem="http://tempuri.org/">
   <soapenv:Header/>
   <soapenv:Body>
      <tem:GetOneDocument>
         <tem:id>%s</tem:id>
      </tem:GetOneDocument>
   </soapenv:Body>
</soapenv:Envelope>
        ''' % file
        r = self.__http_client.post(self.__cfg.url, auth=self.__cfg.get_auth(), data=reqxml,
                                    timeout=30, headers=get_header("GetOneDocument"))
        r.raise_for_status()
        return r.text
