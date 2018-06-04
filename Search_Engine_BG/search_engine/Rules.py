# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/4/16 14:19'
from search_engine import DB_Manager
from search_engine import gengeral
import time
rank_info = ['排行榜', '排名', 'rank', '分布', '名', '名次', '前', '排行',
             '排', '之间', '多', '少', '少于', '以上', '以下', '到', '比', '排前', '最多', '最少']
key_info = ['回答', '提问', '文章', '专栏', '关注人', '被关注', '粉丝', '参加live', '感谢', '点赞', '问题', '关注']
graph_info = ['图', '关系图', '模型', '层次', '层次图', '结构', '关系']
individual_info = ['信息', '基本信息', '介绍']

# 换成去redis中查找
user = []
# with open('user_name.txt', 'r', encoding='utf-8') as f:
#     print("RELOAD")
#     for each in f.readlines():
#         x = each.split(' ')
#         user.append(x[0])


def judge_rule(text):  # 去除停用词
    '''
    :param text: 等待检索判断的文本 单单输入名字也应该有返回
    :return: flag 判断要返回的类型内容 name 人/专栏/话题(token) type_ 类型（与前面对应）
    '''
    flag = 0  # graph 1 rank 2 individual 3  default is graph
    name, type_ = None, None
    for each in text:
        if each in graph_info:
            flag = 1
            break
        elif each in rank_info:
            flag = 2
            break
        elif each in key_info:
            flag = 2
            break
        elif each in individual_info:
            flag = 3
            break
    if flag != 2:
        # type_ = 'user'
        for each in text:
            '''
            By using redis to judge if it's exist to store its name not only urltoken
            '''
            # t1 = time.time()
            if DB_Manager.judge_is_setmember('person_name', each):  # 查看有无 人 话题 专栏 的出现
            # if each in user:
                name = each
                type_ = 'user'
                break
            # print(time.time() - t1)
    elif flag == 2:  # 要计算排名的时候需要用到
        type_ = 'user'  # 默认是用户
        for each in text:
            if each == '用户' or each == '个人':
                type_ = 'user'
                break
            elif each == '话题':
                type_ = 'topic'
                break
            elif each == '专栏':
                type_ = 'column'
                break
    if type_ is None:  # 啥都没找到 则 flag = 0 es 全文搜索
        flag = 0
    return flag, name, type_