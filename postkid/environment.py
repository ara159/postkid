from postkid import PostKidClass

class Enviroment(PostKidClass):
    def __init__(self, name, **kwargs):
        self.name = name
        for name, value in kwargs.items():
            setattr(self, name, value)
    
    def dict(self):
        env_dict = self.__dict__.copy()
        env_dict.pop("name")
        return env_dict
    
    def edit(self, vars_dict):
        for name, value in vars_dict.items():
            setattr(self, name, value)
    
    def __eq__(self, other):
        return self.name == other
