import json
import requests

from postkid import PostKidClass
from postkid.environment import Enviroment


class Request(PostKidClass):
    def __init__(self, **kwgs):
        self.name = None
        self.url = None
        self.method = "GET"
        self.params = {}
        self.headers = {}
        self.body = None
        self.cookies = {}
        self.timeout = 2**16
        self.allow_redirects = True
        self.verify = False
        self.script_pos = None
        for name, value in kwgs.items():
            setattr(self, name, value)
    
    def override_variables(self, enviroment: Enviroment):
        if not enviroment:
            return
        serialized = self.json()
        for name, value in enviroment.dict().items():
            if not value:
                continue
            serialized = serialized.replace("{{" + name + "}}", str(value))
        self.__init__(**json.loads(serialized))
    
    def send(self):
        request_params = self.__dict__.copy()
        request_params.pop("name")
        request_params.pop("script_pos")
        request_params["data"] = request_params.pop("body")
        return requests.request(**request_params)
    
    def __eq__(self, other):
        return self.name == other
