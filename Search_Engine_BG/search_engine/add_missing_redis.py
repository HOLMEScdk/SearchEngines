# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/5/28 3:40'

from search_engine import  DB_Manager
with open('data1_dict.txt', 'w', encoding='utf-8') as f1, open('data_name.txt', 'w', encoding='utf-8') as f2:
    res = DB_Manager.search_mongo('person_table', None, None)
    tot = res.count()
    print(tot)
    cnt = 0
    for each in res:
        if each.get('name') is None:
            print(each['urlToken'])
            continue
        cnt += 1
        # s1 = 'sadd person_success_url %s' % (each['urlToken'])
        # s2 = 'zadd zset_success_url %d %s' % (each['followerCount'], each['urlToken'])
        name = each['name'].replace(' ', '_')
        name = name.replace('\'', '')
        # s3 = 'sadd person_name %s' % (name)
        s4 = '%s 4' % (name)
        if cnt != tot:
            # s1 += '\n'
            # s2 += '\n'
            # s3 += '\n'
            s4 += '\n'
        # f1.write(s1+s2)
        f1.write(s4)
        # f1.write(s4)
        if cnt % 100000 == 0:
            print(cnt)
