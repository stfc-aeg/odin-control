import asyncio
import tornado
import json

from tornado.options import define, options
from tornado.websocket import websocket_connect

define("host", default="127.0.0.1", help="Server host")
define("wsport", default=8888, help="websocket port", type=int)

async def tornado_ws_client(ws_uri):
    ws = await websocket_connect(ws_uri)

    # ws.write_message("Hello!!!")

    # get message 
    get_message = {
        "cmd": "get",
        "paths": ["dummy", "dummy/background_task_count"]
    }
    ws.write_message(json.dumps(get_message))

    # set message
    set_message = {
        "cmd": "set",
        "paths": {"dummy": "abc", "dummy/background_task_count": 123}
    }
    ws.write_message(json.dumps(set_message))

    messages_sent = len(get_message["paths"]) + len(set_message["paths"])
    count = 0

    while count < messages_sent:
        response = await ws.read_message()
        jsonMessage = json.loads(response)
        msg = jsonMessage["response"]
        print(msg)
        count +=1


def main():
    tornado.options.parse_command_line()

    ws_uri = f"ws://{options.host}:{options.wsport}/ws"

    asyncio.run(tornado_ws_client(ws_uri))


if __name__ == '__main__':
    main()
