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
        # self.write_message("Hello!!!!!")

    def on_close(self):
        # self.write_message("Bye!!!!!")
        logging.info("Websocket connection closed from %r", self.request.host)

    def on_message(self, message):
        logging.info("Message received: %r", message)

        # parse json message
        jsonMessage = json.loads(message)
        command = jsonMessage["cmd"]

        if command == "set":
            # for set message
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
                    request = ApiAdapterRequest(None)
                    # get adapter
                    passed_adapter = self.route.adapters.get(adapter_name)
                    # pass path if it exists in message (list will be 2 items), else pass None
                    if len(split_n) == 2:
                        res = passed_adapter.put(path, request)
                    else:
                        res = passed_adapter.put(None, request)
                    # logging.info("%s", res.data)
                    self.write_message(res.data)
                else:
                    # else, output error message
                    logging.info("Adapter '" + adapter_name + "' not found.")


        elif command == "get":
            # for get message
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
                    # logging.info("%s", res.data)
                    self.write_message(res.data)
                else:
                    # else, output error message
                    logging.info("Adapter '" + adapter_name + "' not found.")

        else:
            logging.info("Invalid command: " + command)


        # logging.info(self.route)
        # logging.info(self.route.adapters)
        # logging.info(self.route.handlers)


# class Handler2(RequestHandler):
#     def get(self):
#         self.write("hello")

#     def put(self):
#         self.write("hello")