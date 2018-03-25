# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/19 19:59'

#  参考的调用开源库ip的方法

import requests
import time
import DataManager

class ProxyPool():
    host = 'http://127.0.0.1:8000'  # 代理池请求IP
    ip_pool = []

    def __init__(self):
        self.update_pool()
        # print("初始化")

    def update_pool(self):
        params = {
            # 'count':count,
        }
        response = requests.get(self.host, params=params, timeout=60)
        self.ip_pool = eval(response.content)
        DataManager.remove_all_ip()  # 更新前删除完毕
        #  放到redis中访问
        for each in self.ip_pool:
            DataManager.add_proxy_ip(each)
        # print(self.ip_pool)

    def get_one_ip(self):
        # if len(self.ip_pool) == 0:
        #     self.update_pool()
        if DataManager.get_proxy_size() == 0:
            self.update_pool()
        # 从代理池随机返回一个 ip
        ip = DataManager.get_ip()
        # size = len(self.ip_pool)
        # idx = int(random.random() * size)
        return ip

    def modify_ip(self, ip):
        DataManager.decrease_ip(ip)  # 修改数值

    def delete(self, ip):
        url = "%s/delete"%self.host
        params = {
            'ip':ip[0]
        }
        response = requests.get(url, params=params, timeout=10)
        return response.content

    def sum(self):
        response = requests.get(self.host)
        ips = eval(response.content)
        return len(ips)


if __name__ == '__main__':
    pp = ProxyPool()
    print(pp.sum())
    print(pp.get_one_ip())
    while True:
        time.sleep(100)
        if DataManager.get_proxy_size() <= 10:
            pp.update_pool()
    # print(x.sum(),x.get_one_ip()[0])