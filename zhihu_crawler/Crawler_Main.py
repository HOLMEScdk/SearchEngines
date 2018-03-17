# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/17 12:44'

from zhihu_crawler import general
from zhihu_crawler import DataManager
from zhihu_crawler import HtmlDownload
from zhihu_crawler import Crawler_Start
import time
htmldownload = HtmlDownload.HtmlDownload()
if __name__ == '__main__':
    DataManager.add_waiting_url("li-guan-nan-79")
    while True:
        while DataManager.empty_waiting_url() is True:  # 没有待爬取的url scard equal len
            time.sleep(general.process_waitting)
            general.logger.warn('Redis 无可爬取URL 睡眠\n')
            print("睡眠")
        while DataManager.empty_waiting_url() is False:
            try:
                complet_person, urlToken = Crawler_Start.start_crawler()
            except Exception as e:
                general.logger.info("%s start_crawler 异常" % e)
        print("在等待循环中")
        general.logger.info("在等待循环中")