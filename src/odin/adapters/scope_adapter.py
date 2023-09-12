
import logging

from odin.adapters.adapter import (ApiAdapter, ApiAdapterRequest,
                                   ApiAdapterResponse, request_types)
from odin.util import decode_request_body
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from tornado.ioloop import PeriodicCallback, IOLoop
import time
import json
import numpy as np

class ScopeAdapter(ApiAdapter):

    def __init__(self, **kwargs):

        super(ScopeAdapter, self).__init__(**kwargs)

        self.num_points = 200
        self.range = 20
        self.noise_scale = 0.1
        self.update_interval = 0.1
        self.datax = np.linspace(1, self.range, self.num_points).tolist()
        self.datay = np.zeros(self.num_points).tolist()
        

        self.loop = PeriodicCallback(
            self.generate_data, self.update_interval * 1000
        )

        self.loop.start()

        self.param_tree = ParameterTree({
            "data":{
                "x": (lambda: self.datax, None),
                "y": (lambda: self.datay, None)
            },
            "noise": (self.noise_scale, None),
            "length": (self.num_points, None)
        })

    def get(self, path, request):
        """
        Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """

        try:
            response = self.param_tree.get(path)
            content_type = 'application/json'
            status = 200
        except ParameterTreeError as param_error:
            response = {'response': "Graphing Adapter GET Error: %s".format(param_error)}
            content_type = 'application/json'
            status = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status)

    def generate_data(self):
        logging.debug("GENERATING NEW DATA")
        self.datay =  ((np.sin(self.datax)) + np.random.normal(scale=0.1, size=len(self.datax))).tolist()