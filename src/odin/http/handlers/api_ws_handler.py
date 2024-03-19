import logging
import tornado
import json

# from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler

from odin.http.handlers.base import BaseApiHandler

from odin.adapters.adapter import ApiAdapterRequest

class WsHandler(WebSocketHandler):

    def __init__(self, *args, **kwargs):
        self.route = None
        super(WsHandler, self).__init__(*args, **kwargs)


    def initialize(self, route):
        logging.debug("WSHandler initalize")
        self.route = route


    def open(self):
        logging.info("WebSocket connection opened from %r", self.request.host)


    def on_close(self):
        logging.info("Websocket connection closed from %r", self.request.host)


    def get_message(self, jsonMessage, command):
        for n in (jsonMessage["paths"]):
            # split up passed path 
            split_n = n.split('/', 1)
            # set variables
            adapter_name = split_n[0]
            # if path was passed, set it, if not, set None
            if len(split_n) == 2:
                path = split_n[1]
            else:
                path = "none"
            logging.info("Command: %s, Adapter: %s, Path: %s",
                            command,
                            adapter_name,
                            path)

            # check the adapter exists
            if adapter_name in self.route.adapters:
                # if the adapter exists, perform request
                logging.info("Adapter '" + adapter_name + "' found.")
                request = ApiAdapterRequest(None)
                # get adapter
                passed_adapter = self.route.adapters.get(adapter_name)
                # pass path if it exists in message (list will be 2 items), else pass None
                if len(split_n) == 2:
                    res = passed_adapter.get(path, request)
                else:
                    res = passed_adapter.get(None, request)
                self.write_message(res.data)
            else:
                # else, output error message
                logging.info("Adapter '" + adapter_name + "' not found.")

    def set_message(self, jsonMessage, command):
        for n in (jsonMessage["paths"]):
            # split up passed path
            split_n = n.split('/', 1)
            # set variables
            adapter_name = split_n[0]
            if len(split_n) == 2:
                path = split_n[1]
                set_to = jsonMessage["paths"][adapter_name + "/" + path]
            else:
                path = "none"
                set_to = jsonMessage["paths"][adapter_name]
            logging.info("Command: %s, Adapter: %s, Path: %s, Set-To: %s",
                            command,
                            adapter_name,
                            path,
                            set_to)

            # check the adapter exists
            if adapter_name in self.route.adapters:
                # if the adapter exists, perform request
                logging.info("Adapter '" + adapter_name + "' found.")
                # As the set_to dictionary can have multiple put requests in,
                # loop through each key value pair
                for key, value in set_to.items():
                    # json requires a dictionary, so create a new one
                    new_set = {key: value}
                    request = ApiAdapterRequest(json.dumps(new_set))
                    # get adapter
                    passed_adapter = self.route.adapters.get(adapter_name)
                    # pass path if it exists in message (list will be 2 items), else pass None
                    if len(split_n) == 2:
                        res = passed_adapter.put(path, request)
                    else:
                        res = passed_adapter.put(None, request)
                    self.write_message(res.data)
            else:
                # else, output error message
                logging.info("Adapter '" + adapter_name + "' not found.")


    def on_message(self, message):
        logging.info("Message received: %r", message)

        # parse json message
        jsonMessage = json.loads(message)
        command = jsonMessage["cmd"]

        if command == "set":
            # call set_message function
            self.set_message(jsonMessage, command)

        elif command == "get":
            # call get_message function
            self.get_message(jsonMessage, command)

        else:
            # command is invalid
            logging.info("Invalid command: " + command)
