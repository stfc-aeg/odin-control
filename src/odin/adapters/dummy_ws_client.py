import asyncio
import tornado
import json

from tornado.options import define, options
from tornado.websocket import websocket_connect

define("host", default="127.0.0.1", help="Server host")
define("wsport", default=8888, help="websocket port", type=int)

async def tornado_ws_client(ws_uri):
    ws = await websocket_connect(ws_uri)


    # get message
    get_message = {
        "cmd": "get",
        "paths": ["workshop/background_task/thread_count"]
    }

    ws.write_message(json.dumps(get_message))


    # set message
    set_message = {
        "cmd": "set",
        "paths": {
            "workshop/background_task": {
                "enable": False,
                "interval": 0.5
            }
        }
    }

    ws.write_message(json.dumps(set_message))


    # find out how many messages are expected back
    num_messages = 0

    # add number of set_message requests
    # as the value in set_message["paths"] is a dictionary which
    # can have multiple key/value pairs, find how many pairs
    # there are in order for num_messages to be correct
    for path in (set_message["paths"].keys()):
        num_messages += len(set_message["paths"][path])

    # add number of get_message requests
    num_messages += len(get_message["paths"])
    print("Expecting back " + str(num_messages) + " messages.")

    # retrieve responses
    count = 0
    while count < num_messages:
        response = await ws.read_message()
        jsonMessage = json.loads(response)
        print(jsonMessage)
        count +=1


def main():
    tornado.options.parse_command_line()

    ws_uri = f"ws://{options.host}:{options.wsport}/ws"

    asyncio.run(tornado_ws_client(ws_uri))


if __name__ == '__main__':
    main()
