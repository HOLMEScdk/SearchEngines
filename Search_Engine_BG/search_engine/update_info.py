# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/6/3 17:14'

from search_engine import DB_Manager
import requests
from bs4 import BeautifulSoup as BS
import json
headers = {
    # "Accept-Encoding": "gzip, deflate", #神坑
    'Accept-Language': 'en-US,en;q=0.8',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
}


def store_mongo_person_info(urlToken, user, id_):
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
                                     'school': {
                                         'name': each['school']['name'] if each.get('school') is not None else "",
                                         'photo_url': each['school']['avatarUrl'] if each.get(
                                             'school') is not None else ""}})

    # 职业经历 有
    person['employments'] = []
    for each in user['employments']:
        person['employments'].append(
            {'company': {'name': each['company']['name'] if each.get('company') is not None else "",
                         'photo_url': each['company']['avatarUrl'] if each.get('company') is not None else ""},
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
    res = DB_Manager.mongo_update_data('person_table', id_, person)
    DB_Manager.mongo_update_data('person_json', id_, user)
    return res


def udpate_person(id_, urlToken):
    try:
        URL = 'https://www.zhihu.com/people/'+urlToken+'/activities'
        html = requests.get(URL, headers=headers)
        print("解析")
        s = BS(html.content, 'lxml')
        data = s.find('div', attrs={'id':'data'})['data-state']
        data = json.loads(data)
        user = data['entities']['users'][urlToken]
        res = store_mongo_person_info(urlToken, user, id_)
        return res
    except Exception as e:
        print(e, "更新失败")
