# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/16 19:32'

# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/16 17:47'
from urllib import request
from urllib import parse
import http.cookiejar
import socket
from zhihu_crawler import general
# 暂时无用

class Craweler:
    timeout = 60
    current_proxy = []
    headers = {
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Host': 'www.zhihu.com'
    }
    own_opener = request.build_opener()  # 设置opener 为了更换ip 得到新cookie

    def __init__(self, timeout=None):
        if timeout != None: # 设置超时 socket 全局
            self.timeout = timeout
            socket.setdefaulttimeout(self.timeout)

    def get_html(self, url):
        req = request.Request(url,headers=self.headers)
        response = self.own_opener.open(req, timeout=self.timeout)
        # print(response)
        return response.read()


if __name__ == '__main__':
    c = Craweler()
    s = c.get_html("https://www.zhihu.com/people/gashero/following/columns?page=1")