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
socket.setdefaulttimeout(general.set_socket_timeout)

# proxy_pool = Open_Proxy_.ProxyPool()


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
        self.own_opener = request.build_opener()  # 设置opener 为了更换ip 得到新cookie

    def set_proxy_pool(self, IP):
        general.logger.info("设置代理%s", IP[0])
        handler = request.ProxyHandler({'http': '%s:%d' % (IP[0], IP[1])})
        self.own_opener = request.build_opener(handler)
        self.current_proxy = IP

    def reset_proxyip(self):
        # 获取新代理
        # proxy_pool.modify_ip(self.current_proxy)  # 修改当前的ip分数
        # ip = proxy_pool.get_one_ip()
        DataManager.decrease_ip(self.current_proxy)
        ip = DataManager.get_ip()
        self.set_proxy_pool(ip)

    def get_proxyip(self):
        print(self.current_proxy)

    def download(self, urlToken, page, postdata=None):
        if urlToken is None:
            return False
        url ='%s/people/%s/%s'% (general.host, urlToken, page)
        try:
            if postdata is not None:  # 需要encode
                postdata = str(parse.urlencode(postdata))
                url = '%s/people/%s/%s%s' % (general.host, urlToken, page, postdata,)
            # print(url)
            time.sleep(0.5)
            req = request.Request(url, headers=self.headers)  # Request伪装
            response = self.own_opener.open(req)  # 使用代理
            htm = str(response.read(), encoding="utf-8")
            data = self.html_parse(htm)
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
        time_try = 0
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
                time_try += 1
                if time_try >= 10:
                    return False
                continue
            data = list(data['entities']['users'])
            for each in data:  # 拿到每一页的用户id
                if each == urlToken:
                    continue
                DataManager.add_waiting_url(general.waiting_url, each)  # 增加follower 到等待队列中
                total_follower[attr].append(each)

        if len(total_follower[attr]) > 0:
            DataManager.mongo_output_data(table, total_follower, attr)
        return True

    def html_parse(self, html):
        try:
            s = BS(html, 'lxml')
            data = s.find('div', attrs={'id': 'data'})['data-state']
            data = json.loads(data)
            '''  # 为了加速减去了  原本为了实时性更新数据然后一直用正则
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

    def thread_following_follower(self, urlToken, phrase, table, start_page, each_thread_page, name):  # 其实就是每个爬取一页
        pages = dict()
        pages["page"] = start_page - 1  # 开始先要-1
        cnt = 0
        total_page = each_thread_page if each_thread_page != 0 else 1  # 每一个线程最大执行页面数量
        list_dict = []
        phrase += '?'
        time.sleep(0.5)
        time_try = 0
        while cnt < total_page:
            cnt += 1
            pages["page"] += 1
            try:
                data = self.download(urlToken, phrase, pages)  # 拼接url
                # print(data)
                if data.get("entities") is None or data['entities'].get(name) is None:
                    cnt -= 1
                    pages["page"] -= 1
                    time.sleep(2)
                    continue
            except CustomException:
                general.logger.warn("用户%s设置隐私权限"%urlToken)
                return False
            except Exception as e:
                self.reset_proxyip()
                general.logger.warn("%s 增加用户列表出现异常 用户%s 切换代理" % (e, urlToken))
                cnt -= 1; pages["page"] -= 1
                time.sleep(2)
                time_try += 1
                if time_try >= 10:
                    return  False
                continue
            data = data['entities'][name]
            if name == 'columns':
                for k, v in data.items():  # 拿到每一页 columns 或者 topics
                    if DataManager.judge_is_setmember(general.focus_list_success_url, k) is True:
                        # general.logger.info("%s 专栏已经存放过"%urlToken)
                        continue
                    focus = dict()
                    # 专栏也用redis缓存
                    focus['urlToken'] = k
                    focus["info"] = {'author': {'type': v['author']['type'], 'name': v['author']['name'],
                                                'url': v['author']['url'], 'photo_url': v['author']['avatarUrl']},
                                     'articlesCount': v['articlesCount'],
                                     'title': v['title'], 'description': v['description'], 'followers': v['followers']}
                    list_dict.append(focus)
            else:
                for k, v in data.items():
                    if DataManager.judge_is_setmember(general.focus_list_success_url, k) is True:
                        # general.logger.info("%s 话题已经存放过"%urlToken)
                        continue
                    focus = dict()
                    focus['urlToken'] = k
                    focus['info'] = {'name': v['name'], 'introduction': v['introduction'],'avatarUrl': v['avatarUrl']}
                    list_dict.append(focus)
        if len(list_dict) > 0:
            DataManager.mongo_following_output_data(table, list_dict)
        return True


def download_follower(urlToken, phrase, table, total_num, type_):  # total_num 是同一时间 改话题的总数量 / 一页的20即可
    # 开头这样做为了检查有无用户follower
    total_page = int(abs(total_num-1) / 20) + 1
    # print(total_page)
    try:
        # ht = HtmlDownload()
        # ht.thread_download_follower(urlToken, phrase, table, start_page, total_page)
        ht = HtmlDownload()
        half_page = total_page/general.min_process_num
        start_page = 1
        if type_ == 'user':
            for i in range(int(half_page+0.5)):
                pool = multiprocessing.Pool(processes=general.min_process_num)
                for j in range(general.min_process_num):
                    print("1")
                    pool.apply_async(ht.thread_download_follower, args=(urlToken, phrase, table, start_page, 1))
                    start_page += 1
                pool.close()
                pool.join()
                time.sleep(2)
                if i % 100 == 0:
                   general.logger.warn('用户%s列表查询到第%d页'%(urlToken, i))

        else:
            for i in range(int(half_page + 0.5)):
                pool = multiprocessing.Pool(processes=general.min_process_num)
                for j in range(general.min_process_num):
                    pool.apply_async(ht.thread_following_follower, args=(urlToken, phrase, table, start_page, 1, type_))
                    start_page += 1
                pool.close()
                pool.join()
                time.sleep(2)
                if i % 100 == 0:
                   general.logger.warn('用户%s列表查询到第%d页'%(urlToken, i))

    except Exception as e:
        general.logger.warn("%s download_follower 异常 %s " % (e, urlToken))
        return False
    return True

'''
def thread_start(urlToken, phrase, table,start_page, each_thread_page):
    ht = HtmlDownload()
    ht.reset_proxyip()
    ht.thread_download_follower(urlToken, phrase, table,start_page, each_thread_page)
'''

if __name__ == '__main__':
    pass
    # ht = HtmlDownload()
    # name = "a-hang-xian-sheng-61"  # hong-men-gui-xiu-10
    # # rong-ma-ma-70
    # time_0 = time.time()
    # ans = download_follower(name, 'followers', 'follower_info', 661,'user')
    # # ans = download_follower(name, 'following/topics', 'topics_info', 27, 'topics')
    # print(ans, "结束：", time.time() - time_0)
