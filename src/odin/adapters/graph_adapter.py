"""
Graphing Adapter for Odin Control.
Implements means of monitoring a stream of data, with specified time intervals.
this is done so that GUI elements (such as using chart.js) can be easily implemented

Ashley Neaves, STFC Detector Systems Software Group"""

import logging

from odin.adapters.adapter import (ApiAdapter, ApiAdapterRequest,
                                   ApiAdapterResponse, request_types, response_types)
from odin.util import decode_request_body
from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from tornado.ioloop import PeriodicCallback, IOLoop
import time
import json


class GraphDataset():

    def __init__(self, time_interval, adapter, get_path, retention, location):
        self.time_interval = time_interval
        self.data = []
        self.timestamps = []
        self.adapter_name = adapter
        self.adapter = None
        self.get_path = get_path
        self.retention = retention
        self.location = location

        self.max = max(self.data, default=0)
        self.min = min(self.data, default=0)

        self.data_loop = PeriodicCallback(self.get_data, self.time_interval * 1000)

        logging.debug("Created Dataset %s, interval of %f seconds", location, self.time_interval)

        self.param_tree = ParameterTree({
            "data": (lambda: self.data, None),
            "timestamps": (lambda: self.timestamps, None),
            "interval": (self.time_interval, None),
            "retention": (self.retention * self.time_interval, None),
            "loop_running": (lambda: self.data_loop.is_running(), None),
            "max": (lambda: self.max, None),
            "min": (lambda: self.min, None)
        })

    def get_data(self):
        cur_time = time.strftime("%H:%M:%S", time.localtime())
        response = self.adapter.get(self.get_path, ApiAdapterRequest(None))
        data = response.data[self.get_path.split("/")[-1]]

        self.data.append(data)
        self.timestamps.append(cur_time)
        if len(self.data) > self.retention:
            self.data.pop(0)
            self.timestamps.pop(0)

        self.max = max(self.data)
        self.min = min(self.data)

    def get_adapter(self, adapter_list):
        self.adapter = adapter_list[self.adapter_name]

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)


class AvgGraphDataset(GraphDataset):
    
    def __init__(self, time_interval, retention, source, location):
        super().__init__(time_interval, adapter=None, get_path=None, retention=retention, location=location)
        
        self.source = source
        self.num_points_get = int(self.time_interval / self.source.time_interval)

        self.min_list = []
        self.max_list = []

        logging.debug("Created averaging dataset " + location + ", averaging from %s", self.source)

    def get_data(self):
        cur_time = time.strftime("%H:%M:%S", time.localtime())
        data = self.source.data[-self.num_points_get:]  # slice, get last x elements

        data_min = min(data)
        data_max = max(data)

        # data = list(zip(*data))[1]  # zip the timestamps and data of target list into separate
        data = data = sum(data) / len(data)

        self.min_list.append(data_min)
        self.max_list.append(data_max)

        self.data.append(data)
        self.timestamps.append(cur_time)

        if len(self.data) > self.retention:
            self.data.pop(0)
            self.timestamps.pop(0)

            self.min_list.pop(0)
            self.max_list.pop(0)

        self.min = min(self.min_list)
        self.max = max(self.max_list)

    def get_adapter(self, adapter_list):
        pass  # method empty on purpose as we don't need the adapter for this type of dataset


class GraphAdapter(ApiAdapter):

    def __init__(self, **kwargs):

        super(GraphAdapter, self).__init__(**kwargs)

        self.dataset_config = self.options.get("config_file")

        self.dataset_trees = {}

        self.datasets = {}

        self.param_tree = ParameterTree({})

        self.load_config() 

    def load_config(self):

        logging.debug("loading config file")

        with open(self.dataset_config) as f:
            config = json.load(f)
            
            endpoints = []

            def get_last_dict(dictionary):
                for outer_key, outer_value in dictionary.items():
                    for inner_key, inner_value in outer_value.items():
                        if isinstance(inner_value, dict):
                            get_last_dict(outer_value)
                        else:
                            if (outer_key, outer_value) not in endpoints:
                                endpoints.append((outer_key, outer_value))
                logging.debug(endpoints)
                return endpoints
            #extract innermost dictionary - including it's key
            
            for key, value in get_last_dict(config):
                try:
                    if value.get('average', False):
                        self.add_avg_dataset(value['interval'], value['retention'], value['source'], value['location'])
                    else:
                        self.add_dataset(value['adapter'], value['get_path'], value['interval'], value['retention'], value['location'])
                    
                except KeyError as err:
                    logging.error("Error creating dataset %s: %s", (value['location']), err)

    def add_to_dict(self, location, data, dict):
        param_dict = dict
        parts = location.strip("/").split("/")
        for path_part in parts:
            try:
                if path_part != parts[-1]:
                    param_dict = param_dict[path_part]
                else:
                    param_dict[path_part] = data
            except KeyError:
                param_dict[path_part] = {}
                param_dict = param_dict[path_part]

    def add_dataset(self, adapter, path, interval, retention, location):

        dataset = GraphDataset(
            time_interval=interval,
            adapter=adapter,
            get_path=path,
            retention=retention,
            location=location
            )

        self.add_to_dict(location, dataset.param_tree, self.dataset_trees)
        self.add_to_dict(location, dataset, self.datasets)

        self.param_tree = ParameterTree(self.dataset_trees)

    def add_avg_dataset(self, interval, retention, source, location):

        source_location = source.strip("/").split("/")
        dataset_location = self.datasets
        for path_part in source_location:
            dataset_location = dataset_location[path_part]
        source_dataset = dataset_location
        #getting source dataset - variable location path length

        dataset = AvgGraphDataset(
            time_interval=interval,
            retention=retention,
            source=source_dataset,
            location=location 
        )

        self.add_to_dict(location, dataset.param_tree, self.dataset_trees)
        self.add_to_dict(location, dataset, self.datasets)

        self.param_tree = ParameterTree(self.dataset_trees)

    def initialize(self, adapters):
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)

        logging.debug("Received following dict of Adapters: %s", self.adapters)
        # logging.debug("Getting adapter %s", self.target_adapter)

        endpoints = []

        def iterate_dict(dictionary):
            for key, value in dictionary.items():
                if isinstance(value, dict):
                    iterate_dict(value)
                else:
                    endpoints.append(value)
            return endpoints

        for dataset in iterate_dict(self.datasets):
            dataset.get_adapter(self.adapters)
            dataset.data_loop.start()
        #start loop for each dataset

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
