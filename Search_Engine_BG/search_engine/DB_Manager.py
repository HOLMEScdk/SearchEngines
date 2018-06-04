# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/4/9 14:27'

from search_engine import gengeral
import pymongo
import redis
import time
from elasticsearch import Elasticsearch
from bson.objectid import ObjectId

table_list = ['zhihu_crawler', 'columns_info', 'follower_info', 'following_columns', 'following_info', 'following_topics', 'person_table', 'topics_info']

es = Elasticsearch(host='10.66.3.44', port=9200)
mongo_client = pymongo.MongoClient(host=gengeral.mongo_host, port=gengeral.mongo_port)
mongo_crawler = mongo_client.zhihu_crawler
r0_waitting = redis.Redis(host=gengeral.redis_host, port=gengeral.redis_port, db=0, decode_responses=True)
r2_succeed = redis.Redis(host=gengeral.redis_host, port=gengeral.redis_port, db=0, decode_responses=True)


# redis
def judge_is_setmember(table, url):
    return r2_succeed.sismember(table, url) is True


def get_top_person_rank(table, f_begin=0, f_end=100, score=False):
    return r2_succeed.zrevrange(table, 0, -1, withscores=score)[f_begin:f_end]


# mongo
def search_mongo(table, val, key):  # 执行查询
    collection = mongo_crawler[table]
    queryargs = dict()
    if key is not None:
        queryargs = {key: val}
    if key == '_id':
        queryargs = {key: ObjectId(val)}
    # print('Mongo: ', queryargs)
    # projection = {'followerCount':True, 'name':True, 'urlToken':True}
    projection = {'Time': False}
    res = collection.find(queryargs, projection)
    if res.count() == 0:
        return None
    return res


# es
def search_es(table, val, key, limit_size=10, is_sort=None):
    '''

    :param table: database table
    :param val: value
    :param key: key
    :param limit_size: size
    :return: query_result
    :notice: add sort
    '''
    query = {
        'query': {
            'match': {
                key: val
            },
        },
        'size': limit_size,
        # 'sort': {'followerCount': {'order': 'desc'}}
    }
    if is_sort is not None:  # 作为排序的key
        query['sort'] = {is_sort: {'order': 'desc'}}
    res = es.search(index=table_list[0], doc_type=table, body=query)
    real_info = res['hits']['hits']
    # for each in real_info:
    #     print(each)
    # print(real_info)
    if len(real_info) == 0:
        return None
    return real_info


def search_es_score(table, key, score_range, status, limit_size=10):
    limit_size = 500 if limit_size > 500 else limit_size  # 限定名字
    query = {
        'query': {
            'constant_score':{
                "filter": {
                    "range": {
                        key: {}
                   }
                },
            }
        },
        'size': limit_size,
        'sort': {key: {'order': 'desc'}}
    }
    if len(score_range) == 2:
        query['query']['constant_score']['filter']['range'][key]['gte'] = score_range[0]
        query['query']['constant_score']['filter']['range'][key]['lt'] = score_range[1]
    else:
        '''
        询问分数在5分以上的 则先给5+的 所以查询的时候要从小往大
        '''
        if status == '上':
            query['query']['constant_score']['filter']['range'][key]['gte'] = score_range[0]
            query['sort'][key]['order'] = 'asc'
        else:
            query['query']['constant_score']['filter']['range'][key]['lt'] = score_range[0]
    res = es.search(index=table_list[0], doc_type=table, body=query)
    real_info = res['hits']['hits']
    real_info.append({'total': res['hits']['total']})
    if len(real_info) == 0:
        return None
    return real_info


def search_es_fulltext(table, k_v_dict_list, sort_key, sort_method='desc', is_sort=False):
    query = {
    'query': {
        "bool": {
            "should": [],
        },
    },
        "size": 50,
        'highlight': {
            "fields": {
            }
        }

    }
    if is_sort:
        query['sort'] = {sort_key: {"order": sort_method}}

    for temp in k_v_dict_list:
        query['query']['bool']['should'].append(temp)
        query['highlight']['fields'][list(temp['match'].keys())[0]] = dict() # 设置高亮
    res = es.search(index=table_list[0], doc_type=table, body=query)
    real_info = res['hits']['hits']
    # for each in real_info:
    #     print(each['highlight'])
    if len(real_info) == 0:
        return None
    return real_info


def find_database(kind, val, key):  # 传入值与键查询 为topic column 提供接口
    '''

    :param kind: 数据库表名（类型）
    :param val: 值
    :param key: 键
    :return: 查找的结果集
    '''
    try:
        res = None
        if kind == 'topic':
            pass
        elif kind == 'column':
            pass
        elif kind == 'person':
            # res = search_mongo(gengeral.person_table, val, key)
            res = search_es(gengeral.person_table, val, key)
        return res
    except Exception as e:
        print("Find_database Exception", e)


def get_random_neighbor(url, table):  # 得到对应人的follower/following_info
    search_key = 'followers'
    if 'following' in table:  # 更改查询的内容
        search_key = 'following'
    res_list = []
    # collection = mongo_crawler[table]
    # res_ = collection.find({'urlToken': url}, {'_id': False, search_key: True})  # mongo 精确查找
    # if res_.count() == 0:
    #     return []
    query = {
        'query': {
            'match': {
                'urlToken': url
            },
        },
        # 'size': 5
    }
    res_ = es.search(index=table_list[0], doc_type=table, body=query)
    res_ = res_['hits']['hits']
    if len(res_) == 0:
        return []
    for each_li in res_:  # list
        temp = each_li['_source']  # es
        # temp = each_li
        for each in temp[search_key]:
            if judge_is_setmember(gengeral.person_success_url, each) is True:  # 保证一下层数 Redis 开销
                # print(time.time() - t1)
                # each['photo_url'] = change_photo_url(each['photo_url'])
                res_list.append(each)
            if len(res_list) >= 10:
                break
        break  # 只需要第一个es匹配的就是当前人
    return res_list


def expand_level(kind, token_list):
    '''

    :param kind:  类型
    :param token_list: 每层的每个点的信息
    :return: 每个人的结果信息列表 与 urklToken 列表
    '''
    table = ''
    if kind == 'person':
        table = 'follower_info'
    elif kind == 'column':
        table = 'topic_info'
    # 注意table的改变
    token_dict = {}
    res_list = []
    res_urlToken = []
    for each in token_list:  # 现在扩展的人 each
        token_dict[each] = get_random_neighbor(each, table)  # 得到each的跟随者 最多10人
        '''从list中拿到获得的每个人的信息， 最多3人'''
        if len(token_dict[each]) == 0:
            continue
        cnt = 0
        for token in token_dict[each]:  # 对于each的每个关联者 去拿关联者的信息
            # print("Now level point ",token)
            # res = search_mongo(gengeral.person_table, token, 'urlToken')   # 拿到跟他的每一个人的信息 实际操作的时候应该还要检测一下 这个人有无在redis中 这样保证拿到的一定存在
            res = search_es(gengeral.person_table, token, 'urlToken', 1)  # es
            if res is None:  # 无此人
                continue
            for res_dict in res:
                # temp = res_dict  # mongo
                temp = res_dict['_source']  # es
                temp['id'] = res_dict['_id']
                # print("Temp", temp)
                temp['belong'] = each   # 给每个返回的增加一个上级名字
                cnt += 1
                res_list.append(temp)
                res_urlToken.append(temp['urlToken'])
            if cnt >= 3:  # 这个人的三个满了
                break
    photo_url_key = 'photo_url' if 'topic' not in kind else 'avatarUrl'
    for each in res_list:
        each[photo_url_key] = change_photo_url(each[photo_url_key], kind)
    return res_list, res_urlToken


def store_mongo(table, msg_li):
    collection = mongo_crawler[table]
    cnt = collection.find({}).count()
    if cnt:
        collection.delete_many({})
    collection.insert_many(msg_li)


def update_person_rank():
    '''
    :return: 存储followers的人
    '''
    li = get_top_person_rank(gengeral.zset_success_url)
    msg_li = []
    for token in li:
        msg = search_mongo('person_table', token, 'urlToken')  # 用token找每一个人的msg 然后存进去
        # msg = search_es(gengeral.person_table, token, 'urlToken', 1, is_sort='followerCount')
        if msg is None:
            print("update not found")
            continue
        else:
            # msg = msg[0]['_source']
            msg = msg[0]
            print(msg)
        msg_li.append(msg)  # each val in list is a dict
    # msg_li = sorted(msg_li, key=lambda each: each['followerCount'], reverse=True)
    store_mongo('top_persons', msg_li)


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
        ma = min(100, res.count())
        res = res.sort(key, pymongo.DESCENDING)[:ma]
        store_mongo('top_columns', res)
    elif table == 'topics_info':
        res = collection.find({'followers': {'$ne': None}}, {'_id': False, 'Time': False})
        ma = min(100, res.count())
        res = res.sort(key, pymongo.DESCENDING)[:ma]
        store_mongo('top_topics', res)
    return res


def change_photo_url(url, type_name):
    path_string = 'http://10.66.3.45/'
    if 'column' in type_name:
        path_string += 'columns/'
    elif 'person' in type_name:
        path_string += 'persons/'
    else:
        path_string += 'topics/'
    '''
    在加一个有无这个图片的url
    '''
    return url[url.rfind('/') + 1:]


def mongo_update_data(table, id, dict_attr):
    person_collection = mongo_crawler[table]
    try:
        person_collection.update_one(
            filter={'_id': ObjectId(id)},
            update={'$set': dict_attr},
            upsert=True
        )
        find_res = {"Time": False}
        res_obj = person_collection.find({'_id': ObjectId(id)}, find_res)
        return res_obj[0]
    except Exception as e:
        print(e, " 数据库更新失败")


if __name__ == '__main__':
    res = get_sort_table_key('columns_info', 'info.followers')
    for each in res:
        print(each)
