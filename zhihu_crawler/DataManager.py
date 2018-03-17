# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/17 9:52'
from zhihu_crawler import general
import pymongo
import redis

# mongo
mg_client = pymongo.MongoClient(general.mongo_host, general.mongo_port)
mongo_crawler = mg_client.zhihu_crawler

# Redis
r0_waitting = redis.Redis(host=general.redis_host, port=general.redis_port, db=0)
r1_failed = redis.Redis(host=general.redis_host, port=general.redis_port, db=1)
'''
两个数据结构 一个set集合去重复
一个zset 可以作为之后分数查询的内容
'''
r2_succeed = redis.Redis(host=general.redis_host, port=general.redis_port, db=2)


def empty_waiting_url():
    return r0_waitting.scard(general.waiting_url) == 0


def get_waiting_url():
    new_url = r0_waitting.spop(general.waiting_url)
    return new_url


def add_waiting_url(url):
    r0_waitting.sadd(general.waiting_url, url)
    return True


def judge_is_setmember(setname, url):
    return r2_succeed.sismember(setname, url) is True


def add_person_into_redis(urlToken, user_followers):
    r2_succeed.zadd(general.zset_success_url, urlToken, user_followers)
    r2_succeed.sadd(general.set_success_url, urlToken)
    return True, urlToken


def mongo_search_data(table, urlToken):  # judge whether store in mongo
    person_collection = mongo_crawler[table]
    if person_collection.find({"urlToken": urlToken}).count() != 0:
        return True
    return False


def mongo_output_data(table, person, extra_field=None):  # store in mongo 如果有更新字段要传入额外内容
    person_collection = mongo_crawler[table]
    try:
        if mongo_search_data(table, person['urlToken']) is False:  # count == 0
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
