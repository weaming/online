import json
from tornado import websocket
from util import DictPlus
import user_agents as UA

# better to save out of program
# (ip, host, ua): n
count = {}

# saved for sync information
connect_pool = []


def get_count(type='all_connect', key=None):
    # FOR SITE STATUS =====
    # how many client for one site
    if type == 'client':
        rv = 0
        for k, n in count.items():
            if k[1] == key[1]:
                rv += 1
        return rv

    # how many total connect for one site
    if type == 'site_connect':
        rv = 0
        for k, n in count.items():
            if k[1] == key[1]:
                rv += n
        return rv

    # FOR VISITOR STATUS =====
    # how many pages your current browser opened for one site
    if type == 'client_site_connect':
        return count.get(key, 0)

    # FOR SYSTEM STATUS =====

    # how many client based on (ip, host, user_agent) as key
    if type == 'unique':
        return len(count)

    # how many websocket connect globally
    if type == 'all_connect':
        return sum(count.values())

    return -1


class EchoWebSocket(websocket.WebSocketHandler):
    def prepare(self):
        connect_pool.append(self)

    @property
    def key(self):
        ip = self.request.headers.get('X-Real-IP') or self.request.remote_ip
        host = self.request.headers.get('Origin', '')
        ua = self.request.headers.get('User-Agent')
        ua_parsed = UA.parse(ua)
        return ip, host, ua, str(ua_parsed)

    def send_all(self, msg):
        for handler in connect_pool:
            if isinstance(msg, dict):
                _msg = DictPlus(**msg) + dict(
                    # key=handler.key,
                    client=get_count('client', key=handler.key),
                    client_site_connect=get_count('client_site_connect', key=handler.key),
                    site_connect=get_count('site_connect', key=handler.key),
                    all_connect=get_count('all_connect'),
                )
                text = json.dumps(_msg, ensure_ascii=False)
            else:
                text = str(msg)
            handler.write_message(text)

    def sync_count(self, event=None):
        self.send_all(dict(
            event=event,
            ip=self.key[0],
            host=self.key[1],
            ua=self.key[3],
            all_connect=get_count('all_connect'),
        ))

    def check_origin(self, origin):
        # fix 403 forbidden
        return True

    def open(self):
        count.setdefault(self.key, 0)
        count[self.key] += 1
        print("WebSocket from %s(%s) opened" % self.key[:2])
        self.sync_count('open')

    def on_message(self, message):
        try:
            if message.lower() == 'ping':
                self.write_message('pong')
            else:
                self.write_message(u"You said: " + message)
        except websocket.WebSocketClosedError:
            self.on_close()

    def on_close(self):
        if self in connect_pool:
            connect_pool.remove(self)

        count[self.key] -= 1
        if count[self.key] < 1:
            del count[self.key]

        self.sync_count('close')
        print("WebSocket from %s(%s) closed" % self.key[:2])
