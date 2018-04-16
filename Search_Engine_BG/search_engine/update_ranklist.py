# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/4/13 10:05'
from search_engine import gengeral
from search_engine import DB_Manager
import time
if __name__ == '__main__':
    t = time.time()
    DB_Manager.update_rank()
    table_info = DB_Manager.get_all_table_info('top_person')
    for i, di in enumerate(table_info):
        table_info[i]['number'] = table_info[i]['followerCount']
    print(table_info)
    print(t-time.time())