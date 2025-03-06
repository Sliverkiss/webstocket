import time
from threading import Thread
import json
from xmlrpc.server import SimpleXMLRPCServer

import tornado.websocket
from loguru import logger


class DataStore:
    def __init__(self, maxsize=100):
        self.data = {}
        self.maxsize = maxsize

    def put(self, key, value):
        self.data[key] = value

    def get(self, key, timeout=3):
        end_time = time.time() + timeout
        while key not in self.data:
            remaining = end_time - time.time()
            if remaining <= 0.0:
                return None
        return self.data.pop(key)


connections = {}
TaskId = 0
store = DataStore()


class WeChatSocketHandler(tornado.websocket.WebSocketHandler):

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.userid = None
        self.appid = None

    def data_received(self, chunk: bytes):
        pass

    def open(self):
        try:
            self.userid = self.request.headers['userid'].encode('ISO-8859-1').decode()
            self.appid = self.request.headers['appid']
            logger.debug(f'[新增连接] {self.appid} {self.userid}')
            connections[(self.appid, self.userid)] = self
        except Exception as e:
            import traceback
            logger.error(f'{e} {traceback.format_exc()}')
        # print(f"New client connected. Total connections: {self.request.headers['appid'], len(connections)}")
        # self.send_message(self, "Hello, client!")

    def on_message(self, message):
        message = json.loads(message)
        if not message.get('data'):
            return

        logger.success(f'[接收消息] {message["data"]}')
        store.put(key=f'{TaskId}-{self.request.headers["userid"].encode("ISO-8859-1").decode()}-{self.request.headers["appid"]}', value=message['data'])
        pass

    def on_close(self):
        if connections.get((self.appid, self.userid)):
            del connections[(self.appid, self.userid)]
        # logger.warning(f'[断开连接] {self.request.headers["appid"]} {self.request.headers["userid"]}')
        logger.warning(f'[断开连接] {self.appid} {self.userid}')

    @staticmethod
    def send_message(client, message, timeout: int = 20, params=None):
        if params is None:
            params = {}
        global TaskId
        userid = client.request.headers['userid'].encode('ISO-8859-1').decode()
        appid = client.request.headers['appid']
        logger.debug(f'[发送消息] appid:{appid} userid:{userid} => {message}')
        if connections.get((appid, userid)):
            TaskId += 1
            client.write_message(json.dumps({"TaskId": TaskId, "function_name": message, "params": params}))
            return store.get(key=f"{TaskId}-{userid}-{appid}", timeout=timeout)


def get_connections():
    if len(connections.keys()) != 0:
        sockets_user = [{"appid": i[0], "username": i[1]} for i in connections.keys()]
        return json.dumps(sockets_user, ensure_ascii=False)
    else:
        return json.dumps({"error_msg": "未有连接"}, ensure_ascii=False)


def call(userid: str = "", appid: str = "wxc9c692c952025897", function_name: str = "wx.login()", timeout: int = 20, json_string=None):
    if json_string is None:
        params = {}
    else:
        params = json.loads(json_string)

    end_time = time.time() + timeout
    while connections.get((appid, userid)) is None:
        remaining = end_time - time.time()
        if remaining <= 0.0:
            logger.warning(f'{userid}-{appid} 未连接 => {connections}')
            return json.dumps({"error_msg": f'{appid} 未连接 => {connections}'}, ensure_ascii=False)

    result = WeChatSocketHandler.send_message(connections[(appid, userid)], function_name, timeout=timeout, params=params)
    # print(result)
    return json.dumps(result, ensure_ascii=False)


application = tornado.web.Application([
    (r"/", WeChatSocketHandler),
])


WEBSOCKET_PORT = 22115
application.listen(WEBSOCKET_PORT)
logger.success(f'[websocket 服务端启动] 端口 => {WEBSOCKET_PORT}')
# tornado.ioloop.IOLoop.instance().start()
Thread(target=tornado.ioloop.IOLoop.instance().start).start()

RPC_PORT = 22116
server = SimpleXMLRPCServer(("0.0.0.0", RPC_PORT))
logger.success(f'[RPC 服务端启动] 端口 => {RPC_PORT}')
server.register_multicall_functions()
server.register_function(call, "call")
server.register_function(get_connections, "get_connections")
server.serve_forever()
