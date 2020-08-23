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


DEFAULT_COLLECTION_NAME = "__default__"


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
        self._args = args
    
    def parse(self):
        try:
            opts = 'RI:q:he:p:', ["header", "help"]
            options, remainder = getopt.gnu_getopt(self._args, opts[0], opts[1])
        except getopt.GetoptError as err:
            raise err
        for opt, arg in options:
            if opt == "--header":
                self.show_response_header = True
            if opt == "-R":
                self.show_response_data_only = True
            if opt == "-I":
                self.show_response_meta_only = True
            if opt == "-q":
                for param in arg.split("&"):
                    _param = param.split("=")
                    self.query[_param[0]] = _param[1] if len(_param) > 0  else ""
            if opt == "-p":
                self.collections_folder = arg
            if opt == "-e":
                self.enviroment = arg
            if opt in ("-h", "--help"):
                self._help(); exit(0)
        if len(remainder) == 0:
            self._help()
            raise Exception("collection and request name is required")
        else:
            self.collection_file = remainder[0]
            self.request_name = remainder[1]
            if len(remainder) > 2:
                self.request_vars = {}
                for var in remainder[2:]:
                    name, value = var.split("=")
                    self.request_vars[name] = value
        return self
    
    def _help(self):
        print("""
PostKid v0.1

Ex.: postkid <collection> <request_name> [<var1_name>=<var1_value> <var1_name>=<var1_value> ...]

-h or --help: Show this help message
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
        for name, value in kwargs.items():
            setattr(self, name, value)
    
    def as_dict(self):
        env_dict = self.__dict__.copy()
        name = env_dict.pop("name")
        return {name: env_dict}
    
    def content_as_dict(self):
        env_dict = self.__dict__.copy()
        env_dict.pop("name")
        return env_dict
    
    def edit(self, vars_dict):
        for name, value in vars_dict.items():
            setattr(self, name, value)
    
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
        self.script_pos = None
        for name, value in kwgs.items():
            setattr(self, name, value)
    
    def override_variables(self, enviroment: Enviroment):
        if enviroment is None:
            return
        dump = self._as_raw_json()
        for name, value in enviroment.content_as_dict().items():
            if value is None: continue
            dump = dump.replace("{{" + name + "}}", str(value))
        self.__init__(**json.loads(dump))
    
    def send(self):
        request_params = self.__dict__.copy()
        request_params.pop("name")
        request_params.pop("script_pos")
        request_params["data"] = request_params.pop("body")
        return requestSend(**request_params)
    
    def _as_raw_json(self):
        return json.dumps(self.__dict__, ensure_ascii=False)
    
    def __eq__(self, other):
        return self.name == other
    
    def __repr__(self):
        return parseAsJSON(self.__dict__)


class Collection:
    def __init__(self, path: str):
        self.collection_file = path
        self.tmp_file = self.collection_file.replace(".yaml", ".tmp.yaml")
        self._read_collection_file()
        self._read_requests()
        self._read_environments()
        self._read_variables()
        self._load_tmp_environments()
        for name, value in self.raw_collection.items():
            setattr(self, name, value)
    
    def _read_collection_file(self):
        self.raw_collection = loadYAML(self.collection_file)
        if self.raw_collection is None:
            raise Exception("No content found on collection file")
    
    def _read_requests(self):
        requests = self.raw_collection.pop("requests", [])
        requests = requests if requests is not None else []
        self.requests = [Request(**req) for req in requests]

    def _read_environments(self):
        enviroments = self.raw_collection.pop("enviroments", {})
        enviroments = enviroments.items() if enviroments is not None else {}
        self.enviroments = [
            Enviroment(name, **value) for name,value in enviroments]

    def _read_variables(self):
        variables = self.raw_collection.pop("variables", {})
        variables = variables if variables is not None else {}
        self.enviroments.append(Enviroment(DEFAULT_COLLECTION_NAME, **variables))

    def _load_tmp_environments(self):
        _tmp_environments = {}
        if os.path.exists(self.tmp_file):
            _tmp_environments = loadYAML(self.tmp_file).items()
        self.enviroments_tmp = [
            Enviroment(name, **value) for name, value in _tmp_environments]
        if DEFAULT_COLLECTION_NAME not in self.enviroments_tmp:
            self.enviroments_tmp.append(Enviroment(DEFAULT_COLLECTION_NAME))
    def get_request(self, name: str) -> Request:
        return self.requests[self.requests.index(name)]
    
    def get_enviroment(self, name: str, tmp=False) -> Enviroment:
        if not name:
            name = DEFAULT_COLLECTION_NAME

        if tmp:
            return self.enviroments_tmp[self.enviroments_tmp.index(name)]
        
        else:
            return self.enviroments[self.enviroments.index(name)]
    
    def get_enviroments_as_dict(self, tmp=False):
        result_environment = {}
        environments = self.enviroments
        if tmp:
            environments = self.enviroments_tmp
        for environment in environments:
            result_environment[environment.name] = environment.content_as_dict()
        return result_environment
    
    def edit_enviroment(self, enviroment_name: str, var_name: str, var_value: str, tmp=False):
        try:
            enviroment = self.get_enviroment(enviroment_name, tmp)
            enviroment.edit({var_name: var_value})
        except:
            enviroment = Enviroment(enviroment_name, **{var_name: var_value})
            if tmp:
                self.enviroments_tmp.append(enviroment)
            else:
                self.enviroments.append(enviroment)

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


def edit_enviroment(
        collection: Collection,
        enviroment_name: str,
        var_name: str,
        var_value: str):
    if enviroment_name is None: enviroment_name = DEFAULT_COLLECTION_NAME
    if not isinstance(var_name, (str,)): return
    if not isinstance(var_value, (str,int,float)): return
    if not isinstance(enviroment_name, (str,)): return
    collection.edit_enviroment(enviroment_name, var_name, var_value, True)
    with open(collection.tmp_file, "w") as tmp_file:
        tmp_file.write(yaml.dump(
            collection.get_enviroments_as_dict(True),
            indent=2,
            sort_keys=True,
            default_flow_style=False))


def send_request(
        collection: Collection,
        request_name: str,
        enviroment: str,
        query_params: Dict[str,str],
        request_vars: Dict[str,str],
        show_response_data_only = False,
        show_response_header = False,
        show_response_meta_only = False):
    request = collection.get_request(request_name)
    request.override_variables(Enviroment("request_vars", **request_vars))
    request.override_variables(collection.get_enviroment(enviroment, True))
    request.override_variables(collection.get_enviroment(enviroment))
    request.override_variables(collection.get_enviroment(DEFAULT_COLLECTION_NAME))
    if query_params:
        request.params = query_params
    response = request.send()
    show_results(
        response,
        show_response_data_only,
        show_response_header,
        show_response_meta_only)
    setenv = lambda env, name, value: edit_enviroment(collection, env, name, value)
    setcurenv = lambda name, value: edit_enviroment(collection, enviroment, name, value)
    if request.script_pos is not None:
        eval(request.script_pos, {
            "req": request,
            "res": response,
            "setenv": setenv,
            "setcurenv": setcurenv
        })


def start():
    parameters = Parameters(sys.argv[1:]).parse()
    collection = Collection(
        parameters.collections_folder + 
        ("/" if len(parameters.collections_folder) > 0 else "") +
        parameters.collection_file + ".yaml")
    send_request(
        collection,
        parameters.request_name,
        parameters.enviroment,
        parameters.query,
        parameters.request_vars,
        parameters.show_response_data_only,
        parameters.show_response_header,
        parameters.show_response_meta_only)


if __name__ == "__main__":
    try:
        start()
    except Exception as error:
        print("ERRO:", error)