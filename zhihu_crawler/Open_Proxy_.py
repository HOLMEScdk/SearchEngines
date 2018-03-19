# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/19 19:59'

#  参考的调用开源库ip的方法

import requests
import random
from zhihu_crawler import general
class ProxyPool():
    host = 'http://127.0.0.1:8000'  # 代理池请求IP
    ip_pool = []

    def __init__(self):
        self.update_pool()

    def update_pool(self):
        params = {
            # 'count':count,
        }
        response = requests.get(self.host, params=params, timeout=10)
        self.ip_pool = eval(response.content)

    def get_one_ip(self):
        if len(self.ip_pool) == 0:
            self.update_pool()

        # 从代理池随机返回一个 ip
        size = len(self.ip_pool)
        idx = int(random.random() * size)
        return self.ip_pool[idx]

    def delete(self, ip):
        url = "%s/delete"%self.host
        params = {
            'ip':ip[0]
        }

        response = requests.get(url,params=params,timeout=10)
        return response.content

    def sum(self):
        response = requests.get(self.host)
        ips = eval(response.content)
        return len(ips)


if __name__ == '__main__':
    x = ProxyPool()
    print(x.sum(),x.get_one_ip()[0])