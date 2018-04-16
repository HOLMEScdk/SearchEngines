# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/4/9 14:27'

from search_engine import gengeral
import pymongo
import redis
mongo_client = pymongo.MongoClient(host=gengeral.mongo_host, port=gengeral.mongo_port)
mongo_crawler = mongo_client.zhihu_crawler
r0_waitting = redis.Redis(host=gengeral.redis_host, port=gengeral.redis_port, db=0, decode_responses=True)
r2_succeed = redis.Redis(host=gengeral.redis_host, port=gengeral.redis_port, db=2, decode_responses=True)


# redis
def judge_is_setmember(table, url):
    return r2_succeed.sismember(table, url) is True


def get_top_rank(table, f_begin=0, f_end=20, score=False):
    return r2_succeed.zrevrange(table, 0, -1, withscores=score)[f_begin:f_end]


# mongo
def search_mongo(table, val, key):  # 执行查询
    collection = mongo_crawler[table]
    queryargs = {key: val}
    projection = {'_id': False, 'Time': False}
    res = collection.find(queryargs, projection)
    if res.count() == 0:
        return None
    return res


def find_mongo(kind, val, key):  # 传入值与键查询 为topic column 提供接口
    try:
        res = None
        if kind == 'topic':
            pass
        elif kind == 'column':
            pass
        elif kind == 'user':
            res = search_mongo('person_table', val, key)
        return res
    except Exception as e:
        print("Find Mongo Exception", e)


def get_random_neighbor(url, table):  # 得到对应人的follower/following
    search_key = 'followers'
    if 'following' in table:
        search_key = 'following'
    res_list = []
    collection = mongo_crawler[table]
    res = collection.find({'urlToken': url}, {'_id': False, search_key: True})
    if res.count() == 0:
        return []
    for each_li in res: # list
        for each in each_li[search_key]:
            if judge_is_setmember(gengeral.person_success_url, each) is True:
                res_list.append(each)
            if len(res_list) >= 10:
                break
    return res_list


def expand_level(kind, token_list):  # 扩展每层的人他的节点的信息
    table = ''
    if kind == 'user':
        table = 'follower_info'
    elif kind == 'column':
        table = 'topic_info'
    # 注意table的改变
    token_dict = {}
    res_list = []
    res_urlToken = []
    for each in token_list:  # 现在扩展的人
        token_dict[each] = get_random_neighbor(each, table)  # 得到他的跟随者 最多100人
        '''从list中拿到获得的每个人的信息， 最多3人'''
        if len(token_dict[each]) == 0:
            continue
        cnt = 0
        for token in token_dict[each]:  # 对于这个人的每个关联者 去拿关联者的信息
            res = search_mongo(gengeral.person_table, token, 'urlToken')   # 拿到跟他的每一个人的信息 实际操作的时候应该还要检测一下 这个人有无在redis中 这样保证拿到的一定存在
            if res is None:  # 无此人
                continue
            for res_dict in res:
                res_dict['belong'] = each   # 给每个返回的增加一个上级名字
                cnt += 1
                res_list.append(res_dict)
                res_urlToken.append(res_dict['urlToken'])
            if cnt >= 3:  # 这个人的三个满了
                break
    return res_list, res_urlToken


def store_mongo(table, msg_li):
    collection = mongo_crawler[table]
    cnt = collection.find({}).count()
    if not cnt:
        collection.delete_many({})
    collection.insert_many(msg_li)


def update_rank():
    li = get_top_rank(gengeral.zset_success_url)
    msg_li = []
    for token in li:
        msg = search_mongo('person_table', token, 'urlToken')
        msg_li.append(msg[0])
    store_mongo('top_person', msg_li)


def get_all_table_info(table):
    msg_li = []
    collection = mongo_crawler[table]
    res = collection.find({}, {'_id': False})
    if res.count() == 0:  # 无表
        return None
    for each in res:
        msg_li.append(each)
    return msg_li


def get_sort_table_key(table, key):
    collection = mongo_crawler[table]
    res = []
    if table == 'columns_info':
        res = collection.find({}, {'_id': False, 'Time': False})
        ma = max(20, res.count())
        res = res.sort(key, pymongo.DESCENDING)[:ma]
    return res


if __name__ == '__main__':
    pass
    # res = get_sort_table_key('columns_info', 'info.followers')
    # for each in res:
    #     print(each)
