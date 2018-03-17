# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/17 10:16'

from urllib import request
from urllib import parse
from zhihu_crawler import general
from zhihu_crawler import DataManager
import socket
import json
from bs4 import BeautifulSoup as BS
import re
socket.setdefaulttimeout(general.set_socket_timeout)


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

    def download(self, urlToken, page, postdata=None):
        if urlToken is None:
            return False
        url ='%s/people/%s/%s'% (general.host, urlToken, page)
        try:
            if postdata != None:  # 需要encode
                postdata = parse.urlencode(postdata)
                url = '%s/people/%s/%s%s' % (general.host, urlToken, page, postdata)
            req = request.Request(url, headers=self.headers)
            html = request.urlopen(req).read()
            htm = str(html, encoding="utf-8")
            data, parse_page = self.html_parse(htm)
        except Exception as e:
            general.logger.warn("%s 下载html异常\n" % e)
            return
        return data, parse_page

    def download_follower(self, urlToken, phrase):
        pages = {}
        pages["page"] = 0
        # 开头这样做为了检查有无用户follower
        cnt = 0
        total_page = 1
        total_follower = {}
        phrase += '?'
        try:
            if total_follower.get(urlToken) is None:
                total_follower[urlToken] = []
            while cnt < total_page:
                cnt += 1
                pages["page"] += 1
                data, parse_page = self.download(urlToken, phrase, pages)
                if parse_page is None:
                    break
                data = list(data['entities']['users'])
                for each in data:  # 拿到每一页的用户id
                    if each is None or each is False:
                        break
                    if each == urlToken:
                        continue
                    DataManager.add_waiting_url(each)  # 增加follower 到等待队列中
                    total_follower[urlToken].append(each)

                list_page = parse_page.find_all('button',
                                     class_='Button PaginationButton Button--plain')  # 找到所有的跳转页button 获得最后一个值
                if len(list_page) != 0:  # 每次看下要不要更新
                    digital_button = str(list_page[-1])
                    pattern = re.compile('<[^>]+>')
                    total_page = int(pattern.sub("", digital_button))
                else:
                    general.logger.info("%s Followers/Following 全部添加进redis中" % urlToken)
                    break
        except Exception as e:
            general.logger.info("%e 增加用户列表出现异常" % e)
        return total_follower

    def html_parse(self, html):
        s = BS(html, 'lxml')
        data = s.find('div', attrs={'id': 'data'})['data-state']
        data = json.loads(data)
        return data, s


if __name__ == '__main__':
    ht = HtmlDownload()
    # ans = ht.download_follower("li-guan-nan-79",'following')
    # print(len(ans['li-guan-nan-79']))