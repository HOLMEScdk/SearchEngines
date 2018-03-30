# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/17 10:16'

from urllib import request
from urllib import parse
import general
import DataManager
import math
import multiprocessing
import socket
import json
from bs4 import BeautifulSoup as BS
import threading
import time
socket.setdefaulttimeout(general.set_socket_timeout)


class CustomException(Exception):  # self_define exception
    def __init__(self, warning):
        Exception.__init__(self)
        self.warning = warning


class HtmlDownload(object):

    def __init__(self):

        self.headers = {
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
        handler = request.ProxyHandler({'http': '%s:%d' % (IP[0], IP[1])})  # Notice! this is a https protocol
        self.own_opener = request.build_opener(handler)
        self.current_proxy = IP

    def reset_proxyip(self, flag=0):
        DataManager.decrease_ip(self.current_proxy, flag)
        ip = None
        while ip is None:  # maybe the Proxy_Pool is empty
            ip = DataManager.get_ip()
        self.set_proxy_pool(ip)

    def get_proxyip(self):
        print(self.current_proxy)

    def download(self, urlToken, page, postdata=None):
        if urlToken is None:
            return False
        url ='%s/people/%s/%s'% (general.host, urlToken, page)
        data = {}
        cnt = 10
        while cnt > 0:
            cnt -= 1
            try:
                if postdata is not None:  # 需要encode
                    pos = parse.urlencode(postdata)
                    url = '%s/people/%s/%s%s' % (general.host, urlToken, page, pos)
                req = request.Request(url, headers=self.headers)  # Request伪装
                response = self.own_opener.open(req)  # 使用代理
                htm = str(response.read(), encoding="utf-8")
                data = self.html_parse(htm)
                if data is not None and len(data) != 0:  # 无异常 则正常推出返回 while是给了试错的机会
                    break
            except Exception as e:
                    flag = 0
                    if str(e).find('urlopen error') != -1:
                        flag = 1
                        if str(e).find('Connection refused'):
                            general.logger.info('Delete this ip: %s', self.current_proxy)
                    general.logger.warn("%s 下载html异常 用户 %s\n" % (e, urlToken))
                    self.reset_proxyip(flag)
                    time.sleep(1)
        return data
    '''
    ::urlToken->personID
    ::phrase->following/follower(URL的字段内容)
    ::table-> DataBase stable
    '''
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
        time_try = 0  # Set Time Limitation
        while cnt < total_page:
            cnt += 1
            pages["page"] += 1
            try:
                data = self.download(urlToken, phrase, pages)  # 拼接url
                if data.get("entities") is None or data['entities'].get('users') is None:  # 下面都是对异常的处理 如果是网络原因导致的则应当回退重新执行该页面
                    cnt -= 1
                    pages["page"] -= 1
                    time.sleep(1)
                    continue
                if len(data["entities"]["users"]) == 0:
                    raise CustomException("用户信息设置隐私")
            except CustomException:
                DataManager.add_waiting_url(general.denial_url, urlToken)
                general.logger.warn("用户%s设置隐私权限"%urlToken)
                return False
            except Exception as e:
                self.reset_proxyip()
                general.logger.warn("%s 增加用户列表出现异常 用户%s 切换代理" % (e, urlToken))
                cnt -= 1
                pages["page"] -= 1
                time.sleep(1)
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

        if len(total_follower[attr]) > 0:  # attr作为更新的阈值字段
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
            return None
    '''
    ::name 存储两种 columns or topics
    '''
    def thread_following_follower(self, urlToken, phrase, table, start_page, each_thread_page, name, tot_num=0):  # 其实就是每个爬取一页
        pages = dict()
        pages["page"] = start_page - 1  # 开始先要-1
        cnt = 0
        total_page = each_thread_page if each_thread_page != 0 else 1  # 每一个线程最大执行页面数量
        list_dict = []
        user_focus = {}
        phrase += '?'
        time_try = 0
        num = 1 if tot_num > 0 else -1 # 总数为0的时候则是-1因为0<-1成立 不然的话有一个内容爬取即可
        while cnt < total_page:
            cnt += 1
            pages["page"] += 1
            try:
                data = self.download(urlToken, phrase, pages)  # 拼接url
                if data.get("entities") is None or data['entities'].get(name) is None or len(data['entities'][name]) < num:   # 异常处理内容同上述
                    cnt -= 1
                    pages["page"] -= 1
                    time.sleep(1)
                    continue
            except CustomException:
                DataManager.add_waiting_url(general.denial_url, urlToken)
                general.logger.warn("用户%s设置隐私权限"%urlToken)
                return False
            except Exception as e:
                self.reset_proxyip()
                general.logger.warn("%s 增加用户列表出现异常 用户%s 切换代理" % (e, urlToken))
                cnt -= 1; pages["page"] -= 1
                time.sleep(1)
                time_try += 1
                if time_try >= 10:
                    return False
                continue
            data = data['entities'][name]
            user_focus['urlToken'] = urlToken
            user_focus['following'] = []
            if name == 'columns':
                for k, v in data.items():  # 拿到每一页 columns 或者 topics
                    if DataManager.judge_is_setmember(general.focus_list_success_url, k) is True:  # 专栏已经存放过
                        continue
                    focus = dict()
                    # 专栏也用redis缓存
                    focus['urlToken'] = k
                    focus["info"] = {'author': {'type': v['author']['type'], 'name': v['author']['name'],
                                                'url': v['author']['url'], 'photo_url': v['author']['avatarUrl']},
                                     'articlesCount': v['articlesCount'],
                                     'title': v['title'], 'description': v['description'], 'followers': v['followers']}
                    list_dict.append(focus)
                    user_focus['following'].append({'urlToken': k, 'title': v['title']})
            else:
                for k, v in data.items():
                    if DataManager.judge_is_setmember(general.focus_list_success_url, k) is True:
                        # general.logger.info("%s 话题已经存放过"%urlToken)
                        continue
                    focus = dict()
                    focus['urlToken'] = k
                    focus['info'] = {'name': v['name'], 'introduction': v['introduction'],'avatarUrl': v['avatarUrl']}
                    list_dict.append(focus)
                    user_focus['following'].append({'urlToken': k, 'name': name})
        if len(list_dict) > 0:
            DataManager.mongo_following_output_data(table, list_dict)
        if table == 'topics_info':
            DataManager.mongo_output_data("following_topics", user_focus, extra_field='following')
        else:
            DataManager.mongo_output_data("following_columns", user_focus, extra_field='following')
        return True

'''
::total_num 是同一时间 改话题的总数量 / 一页的20即可
::phrase 是作为url拼接的词
'''


def download_follower(urlToken, phrase, table, total_num, type_):
    # 开头这样做为了检查有无用户follower
    total_page = int(abs(total_num-1) / 20) + 1
    ht = HtmlDownload()
    ip = None
    while ip is None:
        ip = DataManager.get_ip()
    ht.set_proxy_pool(ip)  # set ip
    apart_page = int(math.ceil((total_page / general.max_thread_num) + 0.5))  # thread or multiprocessing?
    start_page = 1
    multi_num = min(total_page, general.max_thread_num)
    if type_ == 'user':
        for i in range(apart_page):
            each_thread_page = 1  # actually one
            thread_list = []
            # pool = multiprocessing.Pool(processes=multi_num)
            for j in range(multi_num):
                t = threading.Thread(target=ht.thread_download_follower, name="Thread%d"% j, args=(urlToken, phrase, table,
                                                                                                    start_page,
                                                                                                    each_thread_page,
                                                                                                    ))
                thread_list.append(t)
                t.start()
                start_page += each_thread_page
            for each in thread_list:
                each.join()
            time.sleep(1)
            if i % 50 == 0:
                general.logger.warn('用户%s关注内容列表查询到第%d页'%(urlToken, i))
            if i >= 100:
                return True
                #     pool.apply_async(ht.thread_download_follower, args=(urlToken, phrase, table, start_page, 1))
                #     start_page += 1
                # pool.close()
                # pool.join()
                # time.sleep(1)
                # if i % 50 == 0:
                #     general.logger.warn('用户%s列表follower/ing查询到第%d页' % (urlToken, i))
                # if i >= 100:
                #     break
                #     each_thread_page = each_thread_page if i != general.max_thread_num-1 else total_page - start_page

    else:
        for i in range(apart_page):
            # pool = multiprocessing.Pool(processes=multi_num)
            each_thread_page = 1
            thread_list = []
            deliver_num = 1 if i != apart_page - 1 else 0
            for j in range(multi_num):
                t = threading.Thread(target=ht.thread_following_follower, name="Thread%d"% j, args=(urlToken, phrase, table,
                                                                                                    start_page,
                                                                                                    each_thread_page,
                                                                                                    type_, deliver_num))  # total_num做为校验抓取内容的准确性
                thread_list.append(t)
                print("DONE2")
                t.start()
                start_page += each_thread_page
            for each in thread_list:
                each.join()
            time.sleep(1)
            if i % 50 == 0:
                general.logger.warn('用户%s关注内容列表查询到第%d页'%(urlToken, i))
            if i >= 100:
                return True
            #     pool.apply_async(ht.thread_following_follower, (urlToken, phrase, table, start_page, 1, type_))
            #     start_page += 1
            # pool.close()
            # pool.join()
            # time.sleep(1)
            # if i % 50 == 0:
            #     general.logger.warn('用户%s关注内容列表查询到第%d页'%(urlToken, i))
            # if i >= 100:
            #     break
    return True


if __name__ == '__main__':
    pass
    # ht = HtmlDownload()
    name = "hao-qi-xin-yan-jiu-suo-58"  # hong-men-gui-xiu-10
    time_0 = time.time()
    # ans = download_follower(name, 'following', 'following_info', 134,'user')
    # ans = download_follower(name, 'following/columns', 'columns_info', 10, 'columns')
    ans = download_follower(name, 'following/topics', 'topics_info', 5, 'topics')
    print(ans, "结束：", time.time() - time_0)
