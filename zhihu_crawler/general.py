# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/15 20:57'

import logging.handlers

# General setting
process_waitting = 20              		# 进程等待时间
set_socket_timeout = 120          		# socket 请求超时时间
Max_Limit = 10              		    # 尝试次数
max_process_num = 6       	        # 抓取最大进程数
min_process_num = 3
waiting_url = 'waiting_url'     		# 待抓取节点集合
waiting_list_url = 'waiting_list_url'   # 等待抓取的个人列表
person_list_success_url = 'person_list_success_url'  # 个人信息列表
focus_list_success_url = 'focus_list_success_url'
zset_success_url = 'zset_success_url'   # url成功有序集合
person_success_url = 'person_success_url' 	# url成功集合
failed_url = 'failed_url'                # 信息抓取失败节点集合
failed_follower = 'failed_follower_set'     # 关注列表抓取失败点
failed_following = 'failed_following_set'
failed_followingfavlists = 'failed_followingfavlists'
failed_followingtopic = 'failed_followingtopic'
failed_followingColumns = 'failed_followingColumns'
host = 'https://www.zhihu.com'		    # 主页面

# DatBase setting
redis_host = 'localhost'				# redis 主机地址
redis_port = 6379					    # redis 主机端口
mongo_host = '127.0.0.1'				# mongodb 主机地址
mongo_port = 27017					    # mongodb 主机端口


# 配置日志
def set_logger():
    LOG_FILE = 'crawler3.log'

    handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1024 * 1024 * 1024, backupCount=5)  # 实例化handler
    fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'
    formatter = logging.Formatter(fmt)  # 实例化formatter
    handler.setFormatter(formatter)  # 为handler添加formatter

    logger = logging.getLogger('crawler')  # 获取名为tst的logger
    logger.addHandler(handler)  # 为logger添加handler
    logger.setLevel(logging.DEBUG)
    return logger


logger = set_logger()

#  logger = FinalLogger.getLogger()
#  logger.debug("this is a debug msg!")
#  logger.info("this is a info msg!")
#  logger.warn("this is a warn msg!")
#  logger.error("this is a error msg!")
#  logger.critical("this is a critical msg!")