# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/4/13 10:05'
from search_engine import gengeral
from search_engine import DB_Manager
import time
cnt = 1
while True:
    '''
    update the top 20 of user and columns and topics
    '''
    DB_Manager.update_person_rank()
    DB_Manager.get_sort_table_key('columns_info', 'info.followers')
    DB_Manager.get_sort_table_key('topics_info', 'followers')
    print("Update %d", cnt)
    cnt += 1
    time.sleep(600)
