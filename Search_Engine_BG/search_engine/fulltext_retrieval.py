# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/6/2 13:30'
from search_engine import DB_Manager
import random
person_search_tag = ['name', 'description', 'headline', 'badge.description']
topic_search_tag = ['info.name', 'info.introduction', ]
column_search_tag = ['info.title', 'info.description']
table_list = ['person_table', 'topics_info', 'columns_info']
operator_tag = ["与", "和", "及"]
random_tag = ['排序', '有序', '顺序']

'''
展示策略 默认按照score 得分最高的两个 然后后面是random 
排序之后 就是得分最高的
'''


def add_search_result(search_type, key, combine_string, operator,is_sort):
    res_list = []
    if search_type == 'person':
        current_search_tag = person_search_tag
        table_name = table_list[0]
    elif search_type == 'topic':
        current_search_tag = topic_search_tag
        table_name = table_list[1]
    else:
        current_search_tag = column_search_tag
        table_name = table_list[2]
    k_v_dict_list = []
    for each in current_search_tag:
        k_v_dict = dict()
        k_v_dict['match'] = {each: {'query': combine_string, 'operator': operator}}
        k_v_dict_list.append(k_v_dict)
    res = DB_Manager.search_es_fulltext(table_name, k_v_dict_list, sort_key='followerCount', is_sort=is_sort)
    if res is None:
        return res_list
    temp_list = []
    for each in res:
        info_dict = each['_source']
        # print(each)
        info_dict['id'] = each['_id']
        temp = {'info': info_dict, 'type': search_type, 'highlight': each['highlight']}
        temp_list.append(temp)
    if is_sort is not True:
        random_set = set()
        random_number = 5
        temp_list_size = len(temp_list)
        if temp_list_size >= random_number:
            while len(random_set) < random_number:
                random_set.add(random.randint(0, temp_list_size-1))
            for each in random_set:
                res_list.append(temp_list[each])
        else:
            res_list = temp_list
    else:
        res_list = temp_list[:5]
    return res_list


def retrieval(text):
    combine_string = text.replace(' ', '')
    is_sort = False
    list_text = text.split(' ')
    for each in random_tag:
        if each in combine_string:
            combine_string = combine_string.replace(each, '')
            is_sort = True
            list_index = -1
            for i, temp in enumerate(list_text):
                if temp == each:
                    list_index = i
            list_text.pop(list_index)
    # print(list_text)
    operator = 'and' if len(list_text) == 1 else 'or'
    for each in operator_tag:
        if each in combine_string:
            operator = 'and'
            break
    print(combine_string, operator, is_sort)
    res_dict, res_list = {}, []
    res_list += add_search_result('person', 'followerCount', combine_string, operator, is_sort)
    res_list += add_search_result('topic', 'followers', combine_string, operator, is_sort)
    res_list += add_search_result('column', 'info.followers', combine_string, operator, is_sort)
    for each in res_list:
        if each['type'] == 'topic':
            each['info']['info']['avatarUrl'] = DB_Manager.change_photo_url(each['info']['info']['avatarUrl'], 'topic')
        elif each['type'] == 'column':
            each['info']['info']['author']['photo_url'] = DB_Manager.change_photo_url(each['info']['info']['author']['photo_url'], 'column')
        elif each['type'] == 'column':
            each['info']['photo_url'] = DB_Manager.change_photo_url(each['info']['photo_url'], 'person')

    res_dict['all'] = res_list
    # print(res_dict)
    return res_dict