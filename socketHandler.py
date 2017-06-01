import json
from tornado import websocket
from util import DictPlus
import user_agents as UA

# better to save out of program
# (ip, host, ua): n
count = {}

# saved for sync information
connect_pool_dict = {}

def get_admin_connect(domain='online.bitsflow.org'):
    for host, connect_list in connect_pool_dict.items():
        if domain in host:
            return connect_list
    return []


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
    @property
    def key(self):
        ip = self.request.headers.get('X-Real-IP') or self.request.remote_ip
        host = self.request.headers.get('Origin', '')
        ua = self.request.headers.get('User-Agent')
        ua_parsed = UA.parse(ua)
        return ip, host, ua, str(ua_parsed)

    def send_all(self, msg):
        self_host = self.key[1]
        targets = connect_pool_dict.get(self_host, [])
        targets += get_admin_connect()
        targets = set(targets)

        for handler in targets:
            key = handler.key
            if isinstance(msg, dict):
                _msg = DictPlus(**msg) + dict(
                    client=get_count('client', key=key),
                    client_site_connect=get_count('client_site_connect', key=key),
                    site_connect=get_count('site_connect', key=key),
                    all_connect=get_count('all_connect'),
                )
                text = json.dumps(_msg, ensure_ascii=False)
            else:
                text = str(msg)
            try:
                handler.write_message(text)
            except websocket.WebSocketClosedError:
                pass


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

        self_host = self.key[1]
        connect_pool_dict.setdefault(self_host, [])
        connect_pool_dict[self_host].append(self)

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
        self_host = self.key[1]
        if self in connect_pool_dict[self_host]:
            connect_pool_dict[self_host].remove(self)

        if self.key in count:
            count[self.key] -= 1
            if count[self.key] < 1:
                del count[self.key]

        self.sync_count('close')
        print("WebSocket from %s(%s) closed" % self.key[:2])

    def __repr__(self):
        return '<ws: {0}, {1}, {3}>'.format(*self.key)
