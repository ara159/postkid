import yaml
import json


class Util:
    @staticmethod
    def load_yaml(path: str):
        content = open(path).read()
        return yaml.load(content, Loader=yaml.Loader)

    @staticmethod
    def dump_yaml(obj) -> str:
        return yaml.dump(
            obj,
            indent = 2,
            sort_keys = True,
            default_flow_style = False)
    
    @staticmethod
    def dump_json(obj) -> str:
        return json.dumps(
            obj = obj,
            indent = 2,
            sort_keys = True,
            ensure_ascii = False,
            default = lambda o: o.__dict__)