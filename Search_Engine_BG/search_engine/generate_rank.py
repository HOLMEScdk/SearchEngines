# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/5/30 9:17'
from search_engine import DB_Manager
import pymongo
import time
import random
rank_info = ['名次', '排名', '前', '名']
score_info = ['分数', '得分', '关注度', '关注量', '人数','关注', '分', '数量', '个数', '数', '以上', '以下']
sensitive_info = ['最多', '最少', '第', '最']
database_info = ['话题', '专栏', '用户', '人']
key_info = ['回答', '提问', '文章', '专栏', '关注人', '被关注', '粉丝', '参加live', '感谢', '点赞', '收藏']


def analyze_meaning(text, number_list):
    '''

    :param text: 用户的输入内容
    :return: 要查询的数据库表 要检索的key 根据前100的排名 还是 分数
    '''
    key, table_name = 'followerCount', 'top_persons'
    search_dict = {'type': 'rank', 'range': number_list, 'meaning': '被关注度','status': '上'} # 先默认根据排名

    for each in ['下', '小', '不超过']: # 有字段 小于, 之下的情形
        if each in text:
            search_dict['status'] = '下'
            break
    if number_list[-1] > 100:  # 值大于100 当作分数处理
        search_dict['type'] = 'score'
    for each in rank_info:
        if each in text and number_list[-1] < 100:
            search_dict['type'] = 'rank'
            break
    for each in score_info:  # 确定查询的方向
        if each in text:
            search_dict['type'] = 'score'  # 根据分数
            break
    for each in sensitive_info:  # 确定里面的数值
        if each in text:
            if each == '第': # 选择一个
                search_dict['range'] = number_list[0]
            elif each == '最多' or each == '最': # 还有个最少
                search_dict['range'] = [1]
                search_dict['type'] = 'rank'
            break
    flag = 0
    for i, each in enumerate(database_info):  # 选择查询的表
        if each in text:
            if i == 0:
                table_name = 'top_topics' if search_dict['type'] == 'rank' else 'topics_info'
            elif i == 1:
                table_name = 'top_columns' if search_dict['type'] == 'rank' else 'columns_info'
            else:
                table_name = 'top_persons' if search_dict['type'] == 'rank' else 'person_table'
            flag = 1
            break
    if flag != 1:
        table_name = 'top_persons' if search_dict['type'] == 'rank' else 'person_table'
    # 选择查询的字段
    if 'person' in table_name:
        for i, each in enumerate(key_info):
            if each in text:
                if each == '回答':
                    key = 'answerCount'
                elif each == '提问':
                    key = 'questionCount'
                elif each == '文章':
                    key = 'articlesCount'
                elif each == '专栏':
                    key = 'columnsCount'
                elif each == '关注人':
                    key = 'followingCount'
                elif each == '被关注' or each == '粉丝':
                    key = 'followerCount'
                elif each == '参加live':
                    key = 'participatedLiveCount'
                elif each == '感谢':
                    key = 'thankedCount'
                elif each == '点赞':
                    key = 'voteupCount'
                elif each == '收藏':
                    key = 'favoritedCount'
                search_dict['meaning'] = each
                break

    elif 'topics' in table_name:
        key = 'followers'
        for each in ['问题', '关注']:
            if each in text:
                key = 'questions' if each == '问题' else 'followers'
                search_dict['meaning'] = each
                break
    else:
        key = 'followers'
        for each in ['文章', '关注']:
            if each in text:
                key = 'articlesCount' if each == '文章' else 'followers'
                search_dict['meaning'] = each
                break
    # print(table_name, key, search_dict)
    return table_name, key, search_dict


def get_rank(table_name, key, search_dict):
    '''
    :param table_name: 数据库的表
    :param key:查询的key
    :param searach_dict:字典 {'type': rank/score, 'range': [a,b]} 根据len判断查的是范围还是前名次
    :return: 排名字典
    '''
    combine_list, res_dict = [], {}  # list作为字典的存放 res为返回的字典
    cnt, redundant = 1, 0  # 进行rank
    search_key = 'info.' + key if 'columns' in table_name else key
    if search_dict['type'] == 'rank':
        # 查询排序好的Mongo
        gap = -10 if search_dict['status'] == '上' else 10  # 针对排名 上即负
        # 显示10名  或者 在他的范围内, 保证 bound1 > bound2
        bound1, bound2 = search_dict['range'][0], max(0, search_dict['range'][0] + gap) \
            if len(search_dict['range']) == 1 else search_dict['range'][1]
        bound1, bound2 = (bound2, bound1) if bound1 > bound2 else (bound1, bound2)
        # print("BOUND1, BOUND2", bound1, bound2)
        res = DB_Manager.search_mongo(table_name, None, None)  # get all
        res = res.sort(search_key, pymongo.DESCENDING)[bound1:bound2]

    else:
        print("search rank in ES")
        # 查询es
        res = DB_Manager.search_es_score(table_name, search_key, search_dict['range'], search_dict['status'])  # get all

    if res is None:
        return None
    res = list(res)
    res_list = res[:-1] if search_dict['type'] == 'score' else res  # 最后一个是记录total的
    if search_dict['type'] == 'score' and search_dict['status'] == '上':
        res_list = list(reversed(res_list))
    tot_size = len(res_list)
    for i, temp in enumerate(res_list):
        each = temp['_source'] if search_dict['type'] == 'score' else temp
        if each.get('_id') is not None:  # 检索mango的
            each['id'] = str(each['_id'])
            each.pop('_id')
        else:
            each['id'] = temp['_id']
        combine_list.append({'rank': cnt, 'info': each})
        if i + 1 != tot_size: # 未检测到最后一个
            if search_dict['type'] != 'score':  # Mongo
                next_value = res_list[i + 1][key] if 'columns' not in table_name else res_list[i + 1]['info'][key]
                current_value = each[key] if 'columns' not in table_name else each['info'][key]
            else:  # 从es中找
                next_value = res_list[i + 1]['_source'][key] if 'columns' not in table_name else res_list[i + 1]['_source']['info'][key]
                current_value = each[key] if 'columns' not in table_name else each['info'][key]
            if next_value < current_value:
                cnt += 1 + redundant  # 后面的没有并列才加
                redundant = 0
            else:
                redundant += 1
    res_dict['result'] = combine_list
    res_dict['count'] = key
    res_dict['meaning'] = search_dict['meaning']
    res_dict['another'] = {'type': search_dict['type'], 'table_name': table_name, 'search_key': search_key,
                           'range': search_dict['range'], 'status': search_dict['status'],
                           'total': res[-1]['total'] if search_dict['type'] == 'score' else 10,
                           'meaning': search_dict['meaning'], 'count': key,
                           'score1': search_dict['range'][0]}
    if len(search_dict['range']) > 1:
        res_dict['another']['score2'] = search_dict['range'][1]
    photo_url_key = 'photo_url' if 'topic' not in table_name else 'avatarUrl'
    for each in res_dict['result']:
        if 'person' in table_name:
            each['info'][photo_url_key] = DB_Manager.change_photo_url(each['info'][photo_url_key], table_name)
        elif 'topic' in table_name:
            each['info']['info'][photo_url_key] = DB_Manager.change_photo_url(each['info']['info'][photo_url_key], table_name)
        else:
            # print(each['info']['info']['author'], '------------')
            each['info']['info']['author'][photo_url_key] = DB_Manager.change_photo_url(each['info']['info']['author'][photo_url_key], table_name)
        # print(each)
    return res_dict


def get_another_rank(parameter_dict):
    table_name = parameter_dict['table_name']
    total_dict = DB_Manager.search_es_score(table_name, parameter_dict['search_key'],
                                            parameter_dict['range'], parameter_dict['status'],
                                            parameter_dict['total'])
    total_list = list(total_dict)[:-1]
    choose_set = set()
    tot = len(total_list)
    if tot >= 10:
        while len(choose_set) < 10:
            choose_set.add(random.randint(0, tot-1))
    else:
        for i in range(tot):  # 不足的直接加
            choose_set.add(i)
    res_dict = {'result':[]}
    combine_list = []
    for each in choose_set:  # 省事情 不排序了
        temp = total_list[each]['_source']
        temp['id'] = total_list[each]['_id']
        combine_list.append({'rank': 1, 'info': temp})
    res_dict['result'] = combine_list
    res_dict['another'] = parameter_dict
    res_dict['count'] = parameter_dict['count']
    res_dict['meaning'] = parameter_dict['meaning']
    photo_url_key = 'photo_url' if 'topic' not in table_name else 'avatarUrl'
    for each in res_dict['result']:
        if 'person' in table_name:
            each['info'][photo_url_key] = DB_Manager.change_photo_url(each['info'][photo_url_key], table_name)
        elif 'topic' in table_name:
            each['info']['info'][photo_url_key] = DB_Manager.change_photo_url(each['info']['info'][photo_url_key], table_name)
        else:
            # print(each['info']['info']['author'], '------------')
            each['info']['info']['author'][photo_url_key] = DB_Manager.change_photo_url(each['info']['info']['author'][photo_url_key], table_name)
    return res_dict


if __name__ == '__main__':
    t1 = time.time()
    table_name = ['top_persons', 'top_columns', 'top_topics']
    res = get_rank('top_persons', 'followerCount', {'type': 'rank', 'range': [5], 'meaning': '被关注度', 'status': '上'})
    # res = get_rank('person_table', 'followerCount', {'type': 'score', 'range': [50000], 'meaning': '被关注度', 'status': '上'})
    # res = get_rank('columns_info', 'followers', {'type': 'score', 'range': [500], 'meaning': '被关注度', 'status': '上'})
    print(time.time() - t1)
    pass
