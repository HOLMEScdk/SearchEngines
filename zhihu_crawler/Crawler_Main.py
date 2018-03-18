# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/17 12:44'

from zhihu_crawler import general
from zhihu_crawler import DataManager
from zhihu_crawler import HtmlDownload
import multiprocessing
from zhihu_crawler import Crawler_Start
from multiprocessing import Pool
import time
import os
htmldownload = HtmlDownload.HtmlDownload()
if __name__ == '__main__':
    # DataManager.add_waiting_url("bing-po-yin-zhen-36")
    # DataManager.add_waiting_url("yang-dong-liang-6")
    # DataManager.add_waiting_url("jieyan")
    # DataManager.add_waiting_url("hu-mars")
    # DataManager.add_waiting_url("python_shequ")
    # DataManager.add_waiting_url("rong-ma-ma-70")
    while True:
        while DataManager.empty_waiting_url() is True:  # 没有待爬取的url scard equal len
            time.sleep(general.process_waitting * 5)
            general.logger.warn('Redis 无可爬取URL 睡眠\n')
            print("睡眠")
        while DataManager.empty_waiting_url() is False:
            general.max_process_num = 6
            try:
                pool = multiprocessing.Pool(processes=general.max_process_num)
                for i in range(general.max_process_num):
                    pool.apply_async(Crawler_Start.start_crawler, args=())
                # 关闭进程池，使其不再接受请求
                pool.close()
                # 等待所有进程请求执行完毕
                pool.join()
                # complet_person, urlToken = Crawler_Start.start_crawler()
            except Exception as e:
                general.logger.info("%s start_crawler 异常" % e)
        print("在等待循环中")
        general.logger.info("在等待循环中")