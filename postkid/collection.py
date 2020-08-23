import os

from postkid import PostKidClass
from postkid.request import Request
from postkid.environment import Enviroment
from postkid.util import Util
from postkid.config import DEFAULT_COLLECTION_NAME


class Collection(PostKidClass):
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
        self.raw_collection = Util.load_yaml(self.collection_file)
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
            _tmp_environments = Util.load_yaml(self.tmp_file).items()
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
            result_environment[environment.name] = environment.dict()
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
