# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/19 19:59'

#  参考的调用开源库ip的方法

import requests
import time
import DataManager


class ProxyPool():
    host = 'http://127.0.0.1:8000/'  # 代理池请求IP
    # host = 'http://piping.mogumiao.com/proxy/api/get_ip_al?appKey=***&count=20&expiryDate=0&format=1'
    ip_pool = []

    def __init__(self):
        self.update_pool()
        # print("初始化")

    def update_pool(self):
        params = {
            # 'count':count,
        }
        DataManager.remove_all_ip()  # 更新前删除完毕
        response = requests.get(self.host, params=params, timeout=15)
        if self.host.find('http://127.0.0.1:8000') != -1:
            self.ip_pool = eval(response.content)
            DataManager.remove_all_ip()  # 更新前删除完毕
            for each in self.ip_pool:
                DataManager.add_proxy_ip(each)
        else:
            self.ip_pool = eval(response.content)
            self.ip_pool = self.ip_pool["msg"]
            ip_list = []
            for each in self.ip_pool:
                port = int(each["port"])
                ip = each["ip"]
                ip_list.append([ip, port])
            for each in ip_list:
                DataManager.add_proxy_ip(each)

    def get_one_ip(self):
        # if len(self.ip_pool) == 0:
        #     self.update_pool()
        if DataManager.get_proxy_size() == 0:
            self.update_pool()
        # 从代理池随机返回一个 ip
        ip = None
        while ip is None:
            ip = DataManager.get_ip()
        return ip

    def print_all(self):
        for each in self.ip_pool:
            print(each)

    def modify_ip(self, ip):
        DataManager.decrease_ip(ip)  # 修改数值

    def delete(self, ip):
        url = "%s/delete"%self.host
        params = {
            'ip': ip[0]
        }
        response = requests.get(url, params=params, timeout=10)
        return response.content

    def sum(self):
        return DataManager.get_proxy_size()


if __name__ == '__main__':
    pp = ProxyPool()
    print(pp.sum())
    print(pp.print_all())
    while True:
        time.sleep(20)
        if DataManager.get_proxy_size() <= 1:
            pp.update_pool()
            print(pp.print_all())
        print(pp.sum())
