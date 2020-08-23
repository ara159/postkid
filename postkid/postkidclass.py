import json
from postkid.util import Util


class PostKidClass:
    def json(self) -> str:
        return Util.dump_json(self.__dict__)
    
    def __repr__(self) -> str:
        return self.json()
