#!/usr/bin/python3
from requests import request as requestSend
from typing import List, Dict
import yaml
import os
import json
import getopt
import sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def loadYAML(path) -> dict:
    return yaml.load(open(path).read(), Loader=yaml.Loader)


def parseAsJSON(data) -> str:
    return json.dumps(
        obj=data,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
        default=lambda obj: obj.__dict__)


def parseEnvVars(params_dump, variables) -> str:
    for name, value in variables.items():
        if value is not None:
            params_dump = params_dump.replace("{{" + name + "}}", str(value))
    return params_dump


class Parameters:
    def __init__(self, args: List[str]):
        self.show_response_header = False
        self.show_response_data_only = False
        self.show_response_meta_only = False
        self.collections_folder = ""
        self.query = {}
        self.enviroment = None
        self.collection_file = None
        self.request_name = None
        self._parse(args)
    
    def _parse(self, args: List[str]):
        try:
            opts = 'RI:q:he:p:', ["header", "help"]
            options, remainder = getopt.gnu_getopt(args, opts[0], opts[1])
        except getopt.GetoptError as err:
            print("ERROR:", err); raise err
        for opt, arg in options:
            if opt == "--header":
                self.show_response_header = True
            if opt == "-R":
                self.show_response_data_only = True
            if opt == "-I":
                self.show_response_meta_only = True
            if opt == "-q":
                for param in arg.split("&"):
                    p = param.split("=")
                    self.query[p[0]] = p[1] if len(p) > 0  else ""
            if opt == "-p":
                self.collections_folder = arg
            if opt == "-e":
                self.enviroment = arg
            if opt in ("-h", "--help"):
                self._help(); raise Exception("Showing the help message")
        if len(remainder) == 0:
            raise Exception("collection and request name is required")
        else:
            self.collection_file = remainder[0]
            self.request_name = remainder[1]
    
    def _help(self):
        print("""
PostKid v0.1

-R: Show only response body
-I: Show only the response meta data (no-body)
-e <enviroment_name> or --mod <mod_name>: Set the mod
-p <collections_folder>: Set folder to search collections files
-q <query_params>: Query params for the request in format "p=abc&q=cba"
--header: Show the response header. By default the header is not show.
--enviroments <path_to_eviroments_files>: Set the path to the enviroments files
""")
    
    def __repr__(self):
        return parseAsJSON(self.__dict__)


class Enviroment:
    def __init__(self, name, **kwargs):
        self.name = name
        for name,value in kwargs.items():
            setattr(self, name, value)
    
    def as_dict(self):
        return self.__dict__
    
    def __eq__(self, other):
        return self.name == other
    
    def __repr__(self):
        return parseAsJSON(self.__dict__)


class Request:
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
        for name,value in kwgs.items():
            setattr(self, name, value)
    
    def override_variables(self, enviroment: Enviroment):
        if enviroment is None: return
        dump = self._as_raw_json()
        for name,value in enviroment.as_dict().items():
            if value is None: continue
            dump = dump.replace("{{" + name + "}}", str(value))
        self.__init__(**json.loads(dump))
    
    def send(self):
        request_params = self.__dict__.copy()
        request_params.pop("name")
        request_params["data"] = request_params.pop("body")
        return requestSend(**request_params)
    
    def _as_raw_json(self):
        return json.dumps(self.__dict__, ensure_ascii=False)
    
    def __eq__(self, other):
        return self.name == other
    
    def __repr__(self):
        return parseAsJSON(self.__dict__)


class Collection:
    def __init__(self, collection_file: str):
        raw_collection = loadYAML(collection_file)
        if raw_collection is None:
            raise Exception("No content found on collection file")
        requests = raw_collection.pop("requests", [])
        requests = requests if requests is not None else []
        self.requests = [Request(**req) for req in requests]
        enviroments = raw_collection.pop("enviroments", {})
        enviroments = enviroments.items() if enviroments is not None else {}
        self.enviroments = [
            Enviroment(name, **value) for name,value in enviroments]
        variables = raw_collection.pop("variables", {})
        variables = variables if variables is not None else {}
        self.variables = Enviroment("__default__", **variables)
        for name,value in raw_collection.items():
            setattr(self, name, value)
    
    def get_request(self, name: str) -> Request:
        return self.requests[self.requests.index(name)]
    
    def get_enviroment(self, name: str) -> Enviroment:
        if name is None or len(name) == 0: return
        return self.enviroments[self.enviroments.index(name)]
    
    def __repr__(self):
        return parseAsJSON(self.__dict__)


def show_results(response, data_only, header, meta_only):
    if not data_only:
        print("Status:", response.status_code)
        print("Url:", response.url)
        if header or meta_only:
            print("Headers:", parseAsJSON(dict(response.headers)))
        print("\n")
    if not meta_only:
        if "application/json" in response.headers.get("content-type", ""):
            print(parseAsJSON(response.json()))
        else:
            print(response.text)

def send_request(
        collection: Collection,
        request_name: str,
        enviroment: str,
        query: Dict[str,str],
        show_response_data_only = False,
        show_response_header = False,
        show_response_meta_only = False):
    request = collection.get_request(request_name)
    request.override_variables(collection.get_enviroment(enviroment))
    request.override_variables(collection.variables)
    if len(query) > 0: request.params = query
    show_results(
        request.send(),
        show_response_data_only,
        show_response_header,
        show_response_meta_only)


def start():
    parameters = Parameters(sys.argv[1:])
    collection = Collection(
        parameters.collections_folder + 
        ("/" if len(parameters.collections_folder) > 0 else "") +
        parameters.collection_file + ".yaml")
    send_request(
        collection,
        parameters.request_name,
        parameters.enviroment,
        parameters.query,
        parameters.show_response_data_only,
        parameters.show_response_header,
        parameters.show_response_meta_only)


if __name__ == "__main__":
    try:
        start()
    except Exception as error:
        print("ERRO:", error)