from parameter_tree import ParameterTree, ParameterAccessor

class MetadataParameterException(Exception):
    pass

class MetadataParameter(object):

    def __init__(self, value, **kwargs):

        self.value = value
        self.metadata = {}

        #Check rw capability of variable
        self.metadata["writeable"] = True
        self.metadata["type"] = type(value).__name__

        if isinstance(value, ParameterAccessor):

            self.metadata["type"] = type(value.get()).__name__

            if not callable(value._set):
                self.metadata["writable"] = False
            

        #Check arguments are valid
        valid_args = ["min", "max", "type", "writable", "available", "units"]
        for kw in kwargs:
            if not kw in valid_args:
                raise MetadataParameterException("Invalid argument: {}".format(kw))

        #Take other values from keyword arguments
        self.metadata.update(kwargs)
                    

class MetadataTree(ParameterTree):

    def set_metadata(path):
