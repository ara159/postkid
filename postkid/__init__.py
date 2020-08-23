import sys

from postkid.config import DEFAULT_COLLECTION_NAME
from postkid.postkidclass import PostKidClass
from postkid.parameters import Parameters
from postkid.collection import Collection
from postkid.environment import Enviroment
from postkid.util import Util


class PostKid:
    def start(self):
        self.parameters = Parameters(sys.argv[1:]).parse()
        self.collection = Collection(self.parameters.collection_file_full_path)
        self.send_request()
        self.show_results()
        self.run_pos_script()

    def show_results(self):
        if not self.parameters.show_response_data_only:
            print("Status:", self.response.status_code)
            print("Url:", self.response.url)
            if self.parameters.show_response_header or self.parameters.show_response_meta_only:
                print("Headers:", Util.dump_json(dict(self.response.headers)))
            print("\n")
        if not self.parameters.show_response_meta_only:
            if "application/json" in self.response.headers.get("content-type", ""):
                print(Util.dump_json(self.response.json()))
            else:
                print(self.response.text)

    def edit_enviroment(self,
            enviroment_name: str,
            var_name: str,
            var_value: str):
        if enviroment_name is None: enviroment_name = DEFAULT_COLLECTION_NAME
        if not isinstance(var_name, (str,)): return
        if not isinstance(var_value, (str,int,float)): return
        if not isinstance(enviroment_name, (str,)): return
        self.collection.edit_enviroment(enviroment_name, var_name, var_value, True)
        with open(self.collection.tmp_file, "w") as tmp_file:
            tmp_file.write(Util.dump_yaml(self.collection.get_enviroments_as_dict(True)))

    def send_request(self):
        self.request = self.collection.get_request(self.parameters.request_name)
        self.request.override_variables(Enviroment("request_vars", **self.parameters.request_vars))
        self.request.override_variables(self.collection.get_enviroment(self.parameters.enviroment, True))
        self.request.override_variables(self.collection.get_enviroment(self.parameters.enviroment))
        self.request.override_variables(self.collection.get_enviroment(DEFAULT_COLLECTION_NAME))
        if self.parameters.query:
            self.request.params = self.parameters.query
        self.response = self.request.send()

    def run_pos_script(self):
        if not self.request.script_pos:
            return
        eval_data = self.eval_functions()
        eval_data["req"] = self.request
        eval_data["res"] = self.response
        eval(self.request.script_pos, eval_data)

    def eval_functions(self):
        def setenv(name, value, environment=None):
            self.edit_enviroment(environment, name, value)
        return {
            "setenv": setenv,
        }
