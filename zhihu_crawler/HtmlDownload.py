# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/17 10:16'

from urllib import request
from urllib import parse
import general
import DataManager
import multiprocessing
import socket
import json
from bs4 import BeautifulSoup as BS
import re
import time
import Open_Proxy_
import threading
socket.setdefaulttimeout(general.set_socket_timeout)

proxy_pool = Open_Proxy_.ProxyPool()


class CustomException(Exception):
    def __init__(self, warning):
        Exception.__init__(self)
        self.warning = warning


class HtmlDownload(object):

    def __init__(self):

        self.headers = {
                    #"Accept-Encoding": "gzip, deflate", #神坑
                   'Accept-Language': 'en-US,en;q=0.8',
                   'Upgrade-Insecure-Requests': '1',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                   'Cache-Control': 'max-age=0',
                   'Connection': 'keep-alive',
                   }
        self.current_proxy = []
        self.ip = ""
        self.own_opener = request.build_opener()  # 设置opener 为了更换ip 得到新cookie

    def set_proxy_pool(self, ip):
        general.logger.info("设置代理%s", ip[0])
        handler = request.ProxyHandler({'http': '%s:%d' % (ip[0], ip[1])})
        self.own_opener = request.build_opener(handler)
        self.current_proxy = ip

    def reset_proxyip(self):
        # 获取新代理
        self.ip = proxy_pool.get_one_ip()
        self.set_proxy_pool(self.ip)

    def get_proxyip(self):
        print(self.ip)

    def download(self, urlToken, page, postdata=None):
        if urlToken is None:
            return False
        url ='%s/people/%s/%s'% (general.host, urlToken, page)
        try:
            if postdata is not None:  # 需要encode
                postdata = str(parse.urlencode(postdata))
                url = '%s/people/%s/%s%s' % (general.host, urlToken, page, postdata,)
            print(url)
            time.sleep(0.5)
            req = request.Request(url, headers=self.headers)  # Request伪装
            response = self.own_opener.open(req)  # 使用代理
            htm = str(response.read(), encoding="utf-8")
            data = self.html_parse(htm)
            # print(data)
            # print(data['entities']['users'])
        except Exception as e:
                # threading.Lock().acquire()
                general.logger.warn("%s 下载html异常 用户 %s\n" % (e, urlToken))
                self.reset_proxyip()
                # print(self.get_proxyip())
                time.sleep(2)
                # threading.Lock().release()
                return {}
        return data

    def thread_download_follower(self, urlToken, phrase, table, start_page, each_thread_page):
        pages = dict()
        pages["page"] = start_page - 1  # 开始先要-1
        # 开头这样做为了检查有无用户follower
        cnt = 0
        total_page = each_thread_page if each_thread_page != 0 else 1  # 每一个线程最大执行页面数量
        total_follower = dict()
        total_follower['urlToken'] = urlToken
        attr = phrase
        phrase += '?'
        total_follower[attr] = []
        non_count = 0
        time.sleep(1)
        while cnt < total_page:
            cnt += 1
            pages["page"] += 1
            try:
                data = self.download(urlToken, phrase, pages)  # 拼接url
                # print(data)
                if data.get("entities") is None:
                    cnt -= 1
                    pages["page"] -= 1
                    time.sleep(2)
                    non_count += 2
                    continue
                if len(data["entities"]["users"]) == 0:
                    raise CustomException("用户信息设置隐私")
            except CustomException:
                general.logger.warn("用户%s设置隐私权限"%urlToken)
                return False
            except Exception as e:
                self.reset_proxyip()
                general.logger.warn("%s 增加用户列表出现异常 用户%s 切换代理" % (e, urlToken))
                cnt -= 1; pages["page"] -= 1
                time.sleep(2)
                continue
            data = list(data['entities']['users'])
            for each in data:  # 拿到每一页的用户id
                if each == urlToken:
                    continue
                DataManager.add_waiting_url(general.waiting_url, each)  # 增加follower 到等待队列中
                total_follower[attr].append(each)
            # if cnt % 100 == 0:
            #     DataManager.mongo_output_data(table, total_follower, attr)
            #     total_follower[attr].clear()
            #     general.logger.warn('用户%s列表查询到第%d页'%(urlToken, cnt))
        if len(total_follower[attr]) > 0:
            DataManager.mongo_output_data(table, total_follower, attr)
        return True

    def html_parse(self, html):
        try:
            s = BS(html, 'lxml')
            data = s.find('div', attrs={'id': 'data'})['data-state']
            data = json.loads(data)
            '''  # 为了加速减去了
            list_page = s.find_all('button',
                                            class_='Button PaginationButton Button--plain')  # 找到所有的跳转页button 获得最后一个值
            total_page = 0
            if len(list_page) != 0:  # 每次看下要不要更新
                digital_button = str(list_page[-1])
                pattern = re.compile('<[^>]+>')
                total_page = int(pattern.sub("", digital_button))
            '''
            return data
        except Exception as e:
            general.logger.warn("%s HTML解析出现异常 " % e)
            return dict()

    def thread_following_follower(self, urlToken, phrase, table, start_page, each_thread_page,name):  # 其实就是每个爬取一页
        pages = dict()
        pages["page"] = start_page - 1  # 开始先要-1
        cnt = 0
        total_page = each_thread_page if each_thread_page != 0 else 1  # 每一个线程最大执行页面数量
        focus = {}
        attr = phrase
        phrase += '?'
        time.sleep(0.5)
        while cnt < total_page:
            cnt += 1
            pages["page"] += 1
            try:
                data = self.download(urlToken, phrase, pages)  # 拼接url
                print(data)
                if data.get("entities") is None:
                    cnt -= 1
                    pages["page"] -= 1
                    time.sleep(1)
                    continue
                if len(data["entities"]["users"]) == 0:
                    raise CustomException("用户信息设置隐私")
            except CustomException:
                general.logger.warn("用户%s设置隐私权限"%urlToken)
                return False
            except Exception as e:
                self.reset_proxyip()
                general.logger.warn("%s 增加用户列表出现异常 用户%s 切换代理" % (e, urlToken))
                cnt -= 1; pages["page"] -= 1
                time.sleep(2)
                continue
            for k, v in data['entities'][name].items():  # 拿到每一页 columns 或者 topics
                # 专栏也用redis缓存
                focus['urlToken'] = k
                focus["info"] = {'author': {'type':v['author']['type'], 'name': v['author']['name']}, 'articlesCount': v['articlesCount']
                            ,'title': v['title'], 'description': v['description'], 'followers': v['followers'], }
        if len(focus) > 0:
            DataManager.mongo_output_data(table, attr)
        return True


def thread_start(urlToken, phrase, table,start_page, each_thread_page):
    ht = HtmlDownload()
    ht.reset_proxyip()
    ht.thread_download_follower(urlToken, phrase, table,start_page, each_thread_page)


def download_follower(urlToken, phrase, table, total_num, type_):  # total_num 是同一时间 改话题的总数量 / 一页的20即可
    # 开头这样做为了检查有无用户follower
    start_page = 1
    total_page = int(abs(total_num-1) / 20) + 1
    print(total_page)
    try:
        # ht = HtmlDownload()
        # ht.thread_download_follower(urlToken, phrase, table, start_page, total_page)
        pool = multiprocessing.Pool(processes=4)
        ht = HtmlDownload()
        if type_ == 'user':
            for i in range(total_page):
                pool.apply_async(ht.thread_download_follower, args=(urlToken, phrase, table, start_page,1))
                start_page += 1

        else:
            print(1123)
            for i in range(total_page):
                pool.apply_async(ht.thread_following_follower, args=(urlToken, phrase, table, start_page,1))
                start_page += 1

        pool.close()
        pool.join()
        '''
            # thread_list = []
            # for i in range(general.max_thread_num):
            #     each_thread_page = each_thread_page if i != general.max_thread_num-1 else total_page - start_page
            #     t = threading.Thread(target=thread_start, name="Thread%d"%i, args=(urlToken, phrase, table,
            #                                                                        start_page, each_thread_page))
            #     thread_list.append(t)
            #     t.start()
            #     start_page += each_thread_page
            #
            # for each in thread_list:
            #     each.join()
        '''
    except Exception as e:
        general.logger.warn("%s download_follower 异常 %s " % (e, urlToken) )
        return False
    return True


if __name__ == '__main__':
    ht = HtmlDownload()
    name = "a-hang-xian-sheng-61"  # hong-men-gui-xiu-10
    # rong-ma-ma-70
    time_0 = time.time()
    # ans = download_follower(name, 'followers', 'follower_info', 661,'user')
    # ans = download_follower(name, 'following/columns', 'columns_info', 8, 'topics')
    ans = ht.thread_download_follower(name, 'following/columns', 'columns_info', 1, 1 )
    print(ans, "结束：", time.time() - time_0)
