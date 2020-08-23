import getopt
from postkid import PostKidClass

class Parameters(PostKidClass):
    def __init__(self, args: [str]):
        self.show_response_header = False
        self.show_response_data_only = False
        self.show_response_meta_only = False
        self.collections_folder = ""
        self.query = {}
        self.enviroment = None
        self.collection_file = None
        self.request_name = None
        self.request_vars = {}
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
                self.help(); exit(0)
        if len(remainder) == 0:
            self.help()
            raise Exception("collection and request name is required")
        else:
            self.collection_file = remainder[0]
            self.request_name = remainder[1]
            self.collection_file_full_path = \
                self.collections_folder + \
                ("/" if self.collections_folder else "") + \
                self.collection_file + \
                (".yaml" if ".yaml" not in self.collection_file else "")
            if len(remainder) > 2:
                self.request_vars = {}
                for var in remainder[2:]:
                    name, value = var.split("=")
                    self.request_vars[name] = value
        return self
    
    def help(self):
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
