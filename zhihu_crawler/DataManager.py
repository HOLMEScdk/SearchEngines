# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/17 9:52'
import general
import pymongo
import redis
from datetime import datetime
# mongo
mg_client = pymongo.MongoClient(general.mongo_host, general.mongo_port)
mongo_crawler = mg_client.zhihu_crawler

# Redis
r0_waitting = redis.Redis(host=general.redis_host, port=general.redis_port, db=0)
# fail 也是r0
'''
两个数据结构 一个set集合去重复
一个zset 可以作为之后分数查询的内容
'''
r2_succeed = redis.Redis(host=general.redis_host, port=general.redis_port, db=2)


def add_failed_url(table,url):
    r0_waitting.sadd(table, url)


def empty_waiting_url(table):
    return r0_waitting.scard(table) == 0


def get_waiting_url(table):
    new_url = r0_waitting.spop(table)
    new_url = str(new_url, encoding='utf-8')
    print(r0_waitting.scard(table))
    return new_url


def add_waiting_url(table, url):
    if judge_is_setmember(general.person_success_url, url) is False:
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


def store_hash_kv(urlToken, attr_dict):
    r0_waitting.hmset(urlToken, attr_dict)


def delete_hash_kv(urlToken):
    r0_waitting.delete(urlToken)


def get_hash_kv(urlToken, key):
    return int(r0_waitting.hget(urlToken, key).decode())

