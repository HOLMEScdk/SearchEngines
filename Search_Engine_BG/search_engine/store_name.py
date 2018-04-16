# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/4/16 10:45'
import pymongo
import time
import datetime
mongo_client = pymongo.MongoClient(host='localhost', port=27017)
mongo_crawler = mongo_client.zhihu_crawler


def search_all():
    collection = mongo_crawler['person_json']
    query = {}
    flag, timestamp = 0, ''
    try:
        with open('log_time.txt', 'r', encoding='utf-8') as f:
                timestamp = list(f.readlines())[-1][:-1]  # get time

    except Exception as e:
        flag = 1
        print(e)
    if not flag:  # 对时间的判断在此
        print(timestamp)
        query = {'Time': {'$gte': datetime.datetime(int(timestamp[:4]), int(timestamp[5:7]), int(timestamp[8:10]),
                                                   int(timestamp[11:13]), int(timestamp[14:16]), int(timestamp[17:19]))
                          }
                 }
    projection = {'urlToken': True, 'name': True, 'Time': True}  # 时间节点的选择上
    res = collection.find(query, projection)
    res.sort('Time', pymongo.ASCENDING)
    cnt = res.count()
    print(cnt)
    return res, cnt


def store_in_file():
    res, cnt = search_all()
    with open('utlToken.txt', 'a+', encoding='utf-8') as f, open('user_name.txt', 'a+', encoding='utf-8') as f1, \
            open('log_time.txt', 'a+', encoding='utf-8') as f2:
        for i, each in enumerate(res):
            f.write(each['urlToken'] + ' 4\n')
            f1.write(each['name'] + ' 4\n')
            if i == cnt - 1:
                f2.write(str(each['Time']) + '\n')


def main():
    store_in_file()


if __name__ == '__main__':
    while True:
        t1 = time.time()
        main()
        print(time.time() - t1)
        time.sleep(3000)