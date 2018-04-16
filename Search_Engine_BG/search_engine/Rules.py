# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/4/16 14:19'
rank_info = ['排行榜', '排名','rank', '分布']
graph_info = ['图','关系图', '模型', '层次','层次图', '结构', '关系']
individual_info = ['信息', '基本信息', '介绍']
# 到后期放到redis中每个人的名字
user = []
with open('user_name.txt', 'r', encoding='uft-8') as f:
    for each in f.readlines():
        x = each.split(' ')
        user.append(x[0])


def judge_rule(text):  # 去除停用词
    '''

    :param text: 等待检索判断的文本
    :return: flag 判断要返回的类型内容 name 人/专栏/话题 type 类型（与前面对应）
    '''
    flag = 0  # graph 1 rank 2 individual 3
    name = None
    for each in text:
        if each in graph_info:
            flag = 1
            break
        elif each in rank_info:
            flag = 2
            break
        elif each in individual_info:
            flag = 3
            break
    for each in text:
        if each in user:
            name = each
    return flag, name, 'user'