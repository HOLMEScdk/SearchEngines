# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/17 9:52'
import general
import pymongo
import redis
import random
from datetime import datetime
# mongo
mg_client = pymongo.MongoClient(general.mongo_host, general.mongo_port)
mongo_crawler = mg_client.zhihu_crawler

# Redis
r0_waitting = redis.Redis(host=general.redis_host, port=general.redis_port, db=0, decode_responses=True)
# fail 也是r0
'''
两个数据结构 一个set集合去重复
一个zset 可以作为之后分数查询的内容
'''
r2_succeed = redis.Redis(host=general.redis_host, port=general.redis_port, db=2, decode_responses=True)


# proxyip管理
def add_proxy_ip(ip,table='proxyzip'):
    r0_waitting.zadd(table, ip, 10)


def get_ip(table='proxyzip'):
    res = r0_waitting.zrangebyscore(table, 0, 11)
    size = len(res)
    idx = int(random.random() * size)
    if size == 0:
        return None
    return eval(res[idx])


def decrease_ip(ip, flag=0,table='proxyzip'):
    r0_waitting.zincrby(table, ip, -1)
    score = r0_waitting.zscore(table, ip)
    if score <= 0 or flag == 1:  # flag == 1 need to be deleted
        r0_waitting.zrem(table, ip)


def remove_all_ip(table='proxyzip'):
    r0_waitting.delete(table)


def get_proxy_size(table='proxyzip'):
    return r0_waitting.zcard(table)
# ------------------------------------ ip


def add_failed_url(table,url):
    r0_waitting.sadd(table, url)


def empty_waiting_url(table):
    return r0_waitting.scard(table) == 0


def get_waiting_url(table):
    new_url = r0_waitting.spop(table)
    # print(r0_waitting.scard(table))
    return new_url


def add_waiting_url(table, url):
    if table == general.denial_url or table == general.denial_url_per or judge_is_setmember(general.person_success_url, url) is False:
        r0_waitting.sadd(table, url)
    return True


def judge_is_setmember(table, url):
    return r2_succeed.sismember(table, url) is True


def add_person_into_redis(urlToken, user_followers):
    r2_succeed.zadd(general.zset_success_url, urlToken, user_followers)
    r2_succeed.sadd(general.person_success_url, urlToken)
    return True, urlToken


def add_person_list_success(urlToken):
    r2_succeed.sadd(general.person_list_success_url, urlToken)


def add_focus_list_success(urlToken):
    r2_succeed.sadd(general.focus_list_success_url, urlToken)


def mongo_search_data(table, urlToken):  # judge whether store in mongo
    person_collection = mongo_crawler[table]
    if person_collection.find({"urlToken": urlToken}).count() != 0:
        return True
    return False


def mongo_output_data(table, person, extra_field=None):  # store in mongo 如果有更新字段要传入额外内容
    person_collection = mongo_crawler[table]
    try:
        if mongo_search_data(table, person['urlToken']) is False:  # count == 0
            person['Time'] = datetime.now()
            person_collection.insert(person)
        else:
            if extra_field is not None:
                person_collection.update(
                    {'urlToken': person['urlToken']},
                    {'$addToSet': {extra_field: {'$each': person[extra_field]}}}
                )  # 追加插入不重复的元素
    except Exception as e:
        print(e, " 数据库插入失败")
        general.logger.error( "%s 数据库插入失败"% e)
    return True


def mongo_following_output_data(table, list_dict):
    try:
        for each in list_dict:
            if mongo_search_data(table, each['urlToken']) is False:
                each['Time'] = datetime.now()
                mongo_crawler[table].insert(each)
                add_focus_list_success(each['urlToken'])
    except Exception as e:
        print(e, " 数据库插入失败")
        general.logger.error("%s 数据库插入%s失败" % (e, table) )
        return False
    return True


# 返回urlToken
def get_table(table):
    zhihu_collection = mongo_crawler[table]
    queryargs = dict()
    projection = dict()
    try:
        if table == 'topics_info': #找到该字段为空的数据
            queryargs = {'followers': None}
            projection = {'urlToken': True, '_id': False, 'info.name': True}
        elif table == 'person_table':
            queryargs = {'name': None}
            projection = {'urlToken': True, '_id': False}
        search_res = zhihu_collection.find(queryargs, projection)
        return search_res
    except Exception as e:
        print(e)


def add_missing_part(table, missing_dict):
    zhihu_collection = mongo_crawler[table]
    try:
        if table == 'topics_info':
            for each in missing_dict:
                zhihu_collection.update(
                    {'urlToken': each},
                    {'$set':{'followers': missing_dict[each]['followers'], 'questions': missing_dict[each]['questions'],
                             'Time': datetime.now()}}
                )
    except Exception as e:
        print(e)


def find_json(url):  # 增加table中的name
    zhihu_collection = mongo_crawler['person_json']
    zhihu_collection2 = mongo_crawler['person_table']  # person的个人信息
    try:
        query = {'urlToken': url}
        projection = {'_id':False, 'name':True}
        search = zhihu_collection.find(query, projection)  # 找到对应的名字
        name = ""
        for each in search:
            zhihu_collection2.update(
                {'urlToken':url},
                {'$set': {'name': each['name'], 'Time': datetime.now()}}
            )
            name = each['name']
        return name
    except Exception as e:
        print(e)




def store_hash_kv(urlToken, attr_dict):
    r0_waitting.hmset(urlToken, attr_dict)


def delete_hash_kv(urlToken):
    r0_waitting.delete(urlToken)


def get_hash_kv(urlToken, key):
    return int(r0_waitting.hget(urlToken, key))

