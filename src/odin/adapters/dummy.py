""" Dummy adapter classes for the ODIN server.

The DummyAdapter class implements a dummy adapter for the ODIN server, demonstrating the
basic adapter implementation and providing a loadable adapter for testing

The IacDummyAdapter class implements a dummy adapter for the ODIN server that can
demonstrate the inter adapter communication, and how an adapter might use the dictionary of
loaded adapters to communicate with them.

Tim Nicholls, STFC Application Engineering
"""
import logging
import asyncio
import tornado
import json

from tornado.ioloop import PeriodicCallback

from odin.adapters.adapter import (ApiAdapter, ApiAdapterRequest,
                                   ApiAdapterResponse, request_types, response_types)
from odin.util import decode_request_body

from tornado.options import define, options
from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler
from tornado.websocket import websocket_connect

define("host", default="127.0.0.1", help="Server host")
define("wsport", default=8889, help="websocket port", type=int)


# class Application(tornado.web.Application):

#     def __init__(self):
#         handlers = [
#             (r"/ws", Handler1),
#             (r"/api", Handler2)
#         ]

#         # for handler in handlers:
#         #     print(handler)

#         settings = dict()

#         super().__init__(handlers, **settings)

# class Handler1(WebSocketHandler):
#     def open(self):
#         logging.info("WebSocket connection opened from %r", self.request.host)
#         # self.write_message("Hello!!!!!")

#     def on_close(self):
#         # self.write_message("Bye!!!!!")
#         logging.info("Websocket connection closed from %r", self.request.host)

#     def send_message(self, message):
#         logging.info("Sending message: %r", message)
#         self.write_message(message)

#     def on_message(self, message):
#         logging.info("Message received: %r", message)
#         self.send_message("Message was received.")


# class Handler2(RequestHandler):
#     def get(self):
#         self.write("hello")

#     def put(self):
#         self.write("hello")


class DummyAdapter(ApiAdapter):
    """Dummy adapter class for the ODIN server.

    This dummy adapter implements the basic operation of an adapter including initialisation
    and HTTP verb methods (GET, PUT, DELETE) with various request and response types allowed.
    """

    def __init__(self, **kwargs):
        """Initialize the DummyAdapter object.

        This constructor Initializes the DummyAdapter object, including launching a background
        task if enabled by the adapter options passed as arguments.

        :param kwargs: keyword arguments specifying options
        """
        super(DummyAdapter, self).__init__(**kwargs)

        # Set the background task counter to zero
        self.background_task_counter = 0

        # Launch the background task if enabled in options
        if self.options.get('background_task_enable', False):
            task_interval = float(
                self.options.get('background_task_interval', 1.0)
                )
            logging.debug(
                "Launching background task with interval %.2f secs", task_interval
            )
            self.background_task = PeriodicCallback(
                self.background_task_callback, task_interval * 1000
            )
            self.background_task.start()

        logging.debug('DummyAdapter loaded')

    def initialize(self, adapters):
        logging.debug("DummyAdapter initialized with %d adapters", len(adapters))

    def background_task_callback(self):
        """Run the adapter background task.

        This simply increments the background counter and sleeps for the specified interval,
        before adding itself as a callback to the IOLoop instance to be called again.

        :param task_interval: time to sleep until task is run again
        """
        logging.debug(
            "%s: background task running, count = %d", self.name, self.background_task_counter)
        self.background_task_counter += 1

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        """Handle an HTTP GET request.

        This method handles an HTTP GET request, returning a JSON response. To facilitate
        testing of the background task, if the URI path is set appropriately, the task
        counter is returned in the JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        if path == 'background_task_count':
            response = {'response': {
                'background_task_count': self.background_task_counter}
            }
        else:
            response = {'response': 'DummyAdapter: GET on path {}'.format(path)}
        
        logging.debug("******************message get**********")

        content_type = 'application/json'
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)


    @request_types('application/json', 'application/vnd.odin-native')
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        """Handle an HTTP PUT request.

        This method handles an HTTP PUT request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = {'response': 'DummyAdapter: PUT on path {}'.format(path)}
        content_type = 'application/json'
        status_code = 200

        logging.debug("******************message set**********")

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def delete(self, path, request):
        """Handle an HTTP DELETE request.

        This method handles an HTTP DELETE request, returning a JSON response.

        :param path: URI path of request
        :param request: HTTP request object
        :return: an ApiAdapterResponse object containing the appropriate response
        """
        response = 'DummyAdapter: DELETE on path {}'.format(path)
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, status_code=status_code)

    def cleanup(self):
        """Clean up the state of the adapter.

        This method cleans up the state of the adapter, which in this case is
        trivially setting the background task counter back to zero for test
        purposes.
        """
        logging.debug("DummyAdapter cleanup: stopping background task")
        self.background_task.stop()
        self.background_task_counter = 0


class IacDummyAdapter(ApiAdapter):
    """Dummy adapter class for the Inter Adapter Communication changes.

    This dummy adapter impelements the basic operations of GET and PUT,
    and allows another adapter to interact with it via these methods.
    """

    def __init__(self, **kwargs):
        """Initialize the dummy target adapter.

        Create the adapter using the base adapter class.
        Create an empty dictionary to store the references to other loaded adapters.
        """

        super(IacDummyAdapter, self).__init__(**kwargs)
        self.adapters = {}

        logging.debug("IAC Dummy Adapter Loaded")

    @response_types("application/json", default="application/json")
    def get(self, path, request):
        """Handle a HTTP GET Request

        Call the get method of each other adapter that is loaded and return the responses
        in a dictionary.
        """
        logging.debug("IAC Dummy Get")
        response = {}
        request = ApiAdapterRequest(None, accept="application/json")
        for key, value in self.adapters.items():
            logging.debug("Calling Get of %s", key)
            response[key] = value.get(path=path, request=request).data
        logging.debug("Full response: %s", response)
        content_type = "application/json"
        status_code = 200

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

    @request_types("application/json", "application/vnd.odin-native")
    @response_types("application/json", default="application/json")
    def put(self, path, request):
        """Handle a HTTP PUT request.

        Calls the put method of each other adapter that has been loaded, and returns the responses
        in a dictionary.
        """
        logging.debug("IAC DUMMY PUT")
        body = decode_request_body(request)
        response = {}
        request = ApiAdapterRequest(body)

        for key, value in self.adapters.items():
            logging.debug("Calling Put of %s", key)
            response[key] = value.put(path="", request=request).data
        content_type = "application/json"
        status_code = 200

        logging.debug(response)

        return ApiAdapterResponse(response, content_type=content_type,
                                  status_code=status_code)

    def initialize(self, adapters):
        """Initialize the adapter after it has been loaded.

        Receive a dictionary of all loaded adapters so that they may be accessed by this adapter.
        Remove itself from the dictionary so that it does not reference itself, as doing so
        could end with an endless recursive loop.
        """

        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)

        logging.debug("Received following dict of Adapters: %s", self.adapters)


# async def main():
#     tornado.options.parse_command_line()
#     app = Application()
#     app.listen(options.wsport)

#     # ws_uri = f"ws://{options.host}:{options.wsport}/ws"
#     # ws = websocket_connect(ws_uri)

#     await asyncio.Event().wait()


# if __name__ == "__main__":
#     asyncio.run(main())
