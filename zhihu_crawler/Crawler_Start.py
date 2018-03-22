# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/16 19:43'

import socket
import general
import DataManager
import HtmlDownload
import Open_Proxy_
import os
import time
import multiprocessing
from datetime import datetime
socket.setdefaulttimeout(general.set_socket_timeout)
html_download = HtmlDownload.HtmlDownload()
proxy_pool = Open_Proxy_.ProxyPool()


def start_crawler():
    # print("进程号%s 时间%s"%(os.getpid(), datetime.now()))
    if DataManager.empty_waiting_url(general.waiting_url) is True:
        time.sleep(general.process_waitting)
        general.logger.warn('Redis 无可爬取URL 当前进程睡眠\n')
    urlToken = DataManager.get_waiting_url(general.waiting_url)   # id
    # urlToken = str(new_token, encoding='utf-8')  # !!!!!!!!!!!!!!encoding
    general.logger.warn("开始访问用户 %s \n" % urlToken)
    now_cnt = general.Max_Limit
    user_followers = 0
    ip = proxy_pool.get_one_ip()
    html_download.set_proxy_pool(ip)
    while now_cnt > 0:
        now_cnt -= 1
        if DataManager.judge_is_setmember(general.person_success_url, urlToken):
            general.logger.warn("%s redis已经存在该用户\n" % urlToken)
            return
        try:
            # crawl = Crawler_Init.Craweler()
            flag = get_new_person_info(urlToken)
            if flag == "DataBaseExists":  # 存储过数据
                general.logger.info("%s 数据库已存储过\n" % urlToken)
                return
            elif flag == "PageError":
                 # 不能跳出去 要10次都None 那就结束
                time.sleep(0.5)
                continue
            elif flag == "SetPrivacy":
                break
            elif flag == "Succeed":
                DataManager.add_waiting_url(general.waiting_list_url, urlToken)  # 个人列表等待队列
                DataManager.add_person_into_redis(urlToken, user_followers)
                return True
        except Exception as e:
            general.logger.warn("%s Failed, Times can try %d USER %s\n" % (e, now_cnt, urlToken))
            time.sleep(1)
    else:  # Failed
        general.logger.error('%d ALL FAILED，put into in the fail set %s \n' % (general.Max_Limit, urlToken))
        DataManager.add_failed_url(general.failed_url, urlToken)
        return False
    # Succeed
    return False


def get_new_person_info(urlToken, crawler=None):
     # 理解opener 与 Request
    # html = crawl.get_html(url_act)
    data = html_download.download(urlToken, "activities")  # 返回json
    if data.get("entities") is None:  # 页面获取出错
        return "PageError"
    if len(data['entities']['users']) == 0:  # 用户设置了权限
        return "SetPrivacy"
    user = data['entities']['users'][urlToken]
    # person = {}
    try:
        person = store_mongo_person_info(urlToken, user)
        if person is False:  # 不用再次访问他的列表了
            return "DataBaseExists"
    except Exception as e:
        general.logger.warn("%s 获取个人信息出现异常 用户%s\n" % (e, urlToken))
    # 暂未解决的性能问题 调度上不好控制 需要爬取两次所有用户的following follower  将就过了
    # store_focus_list(urlToken, "Following", general.failed_following, user["followerCount"])
    # store_focus_list(urlToken, "Follower", general.failed_follower, user["followingCount"])
    return "Succeed"

'''
def store_focus_list(urlToken, phrase, set_name, total_num):
    cnt = 10
    while cnt > 0:
        cnt -= 1
        flag = False
        try:
            if phrase == 'Following':
                if DataManager.mongo_search_data('follower_info', urlToken) is False:
                    flag = HtmlDownload.download_follower(urlToken, 'followers', "follower_info", total_num)
            else:
                if DataManager.mongo_search_data('following_info', urlToken) is False:
                    flag = HtmlDownload.download_follower(urlToken, 'following', "following_info", total_num)
            if flag is True:
                general.logger.info("%s %s 全部添加进redis中" % (urlToken, phrase) )
                break
        except Exception as e:
            general.logger.warn("%s 获取个人%s列表出现异常 用户%s 剩余次数 %d\n" % (e, phrase, urlToken, cnt))
            time.sleep((10 - cnt) * 2)
    else:  # failed
        DataManager.add_failed_url(set_name, urlToken)

'''
'''
存储个人信息 及 其following/followers
'''


def store_mongo_person_info(urlToken, user):
    if DataManager.mongo_search_data('person_table', urlToken) is True:
        return False
    person = {}
    person['urlToken'] = urlToken
    person['userType'] = user['userType']
    # 追加个人信息
    # badge
    person['badge'] = []
    for each in user['badge']:
        topics = []
        if each.get('topics') is not None:
            for top in each['topics']:
                topics.append(top['name'])
        person['badge'].append({'description': each['description'], 'topics': topics,
                                'type': each['type'] if each.get('type') is not None else ''})
    # 用户的headline 有
    person['headline'] = user['headline']
    # 个人简介 有
    person['description'] = user['description']
    # 教育经历 有
    person['educations'] = []
    for each in user['educations']:
        person['educations'].append({'major': each['major']['name'] if each.get('major') is not None else "",
                                     'school': {'name': each['school']['name'] if each.get('school') is not None else "" ,
                                                'photo_url': each['school']['avatarUrl'] if each.get('school') is not None else ""}})

    # 职业经历 有
    person['employments'] = []
    for each in user['employments']:
        person['employments'].append({'company':{'name':each['company']['name'] if each.get('company') is not None else "",
                                                 'photo_url':each['company']['avatarUrl'] if each.get('company') is not None else ""},
                                      'job': each['job']['name'] if each.get('job') is not None else ""})
    # 居住地 有
    person['locations'] = []
    for each in user['locations']:
        person['locations'].append({'name': each['name']})
    # 所在行业 无
    person['business'] = []
    if user.get('business') is not None:
        li = []
        if type(user['business']) is dict:
            li.append(user['business'])
        else:
            li = user['business']
        for each in li:
            person['business'].append({'name': each['name']})

    # 文章被收藏数
    person['favoritedCount'] = user['favoritedCount']
    # 回答数量
    person['answerCount'] = user['answerCount']
    # 提问数
    person['questionCount'] = user['questionCount']
    # 文章数
    person['articlesCount'] = user['articlesCount']
    # 专栏数
    person['columnsCount'] = user['columnsCount']
    # 粉丝
    person['followerCount'] = user['followerCount']
    # 关注的专栏数
    person['followingColumnsCount'] = user['followingColumnsCount']
    # 他关注的个数
    person['followingCount'] = user['followingCount']
    # 关注的收藏夹
    person['followingFavlistsCount'] = user['followingFavlistsCount']
    # 关注的问题
    person['followingQuestionCount'] = user['followingQuestionCount']
    # 关注话题
    person['followingTopicCount'] = user['followingTopicCount']
    # 举办的live
    person['hostedLiveCount'] = user['hostedLiveCount']
    # 参加的live
    person['participatedLiveCount'] = user['participatedLiveCount']
    # 参与公共编辑数
    person['logsCount'] = user['logsCount']
    # 获得点赞数
    person['voteupCount'] = user['voteupCount']
    # 感谢数
    person['thankedCount'] = user['thankedCount']
    # -1 无性别 0 woman 1 man
    person['gender'] = user['gender']
    person['photo_url'] = user['avatarUrl']
    DataManager.mongo_output_data('person_table', person)
    DataManager.mongo_output_data('person_json', user)
    attr_dict = {
        'followerCount': person['followerCount'],
        'followingColumnsCount': person['followingColumnsCount'],
        'followingTopicCount': person['followingTopicCount'],
        'followingCount': person['followingCount']
    }
    DataManager.store_hash_kv(urlToken, attr_dict)
    return True


if __name__ == '__main__':
    # DataManager.add_waiting_url(general.waiting_url, "bing-po-yin-zhen-36")
    # DataManager.add_waiting_url(general.waiting_url, "yang-dong-liang-6")
    # DataManager.add_waiting_url(general.waiting_url, "jieyan")
    # DataManager.add_waiting_url(general.waiting_url, "hu-mars")
    # DataManager.add_waiting_url(general.waiting_url, "python_shequ")
    DataManager.add_waiting_url(general.waiting_url, "rong-ma-ma-70")
    while True:
        while DataManager.empty_waiting_url(general.waiting_url) is True:  # 没有待爬取的url scard equal len
            time.sleep(general.process_waitting * 5)
            general.logger.warn('Redis 无可爬取URL 睡眠\n')
            print("睡眠")
        while DataManager.empty_waiting_url(general.waiting_url) is False:
            try:
                pool = multiprocessing.Pool(processes=general.max_process_num)
                for i in range(100):
                    pool.apply_async(start_crawler, args=())
                pool.close()
                pool.join()
                # complet_person, urlToken = Crawler_Start.start_crawler()
            except Exception as e:
                general.logger.info("%s start_crawler 异常" % e)
        print("在等待循环中")
        general.logger.info("在等待循环中")

