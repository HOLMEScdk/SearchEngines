# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/16 19:32'

# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/16 17:47'
from urllib import request
from urllib import parse
import socket
from zhihu_crawler import Open_Proxy_
from zhihu_crawler import general
open_proxy = Open_Proxy_.ProxyPool()
socket.setdefaulttimeout(general.set_socket_timeout)


class Crawler_proxy():
    timeout = 60


    def __init__(self, timeout=None):
        pass




if __name__ == '__main__':
    pass