# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/4/9 14:26'

from search_engine import DB_Manager
import time
import json

level = ['', 'first', 'second', 'third']


def get_graph(kind, name, urlToken=None):
    '''

    :param kind:  类型
    :param name: 查找名字
    :param urlToken: id
    :return: 关系字典
    '''
    try:
        res = DB_Manager.find_mongo(kind, name, 'name')  # 应改为去es检索
        if res is None:
            return None
        json_dict = {}
        token_list = []
        for each in res:
            each['belong'] = 'root'  # 第一层是root
            json_dict.setdefault(level[1], []).append(each)
            token_list.append(each['urlToken'])
            break # 防止名字重复 只拿一个

        for i in range(2, 4):
            level_res, token_list = DB_Manager.expand_level(kind, token_list)  # 得到新的每一层的结果 结构: [{}, {}]
            if level_res is None:
                break
            json_dict[level[i]] = level_res
        # print(json_dict)
        # print(len(json_dict[level[3]]))
        # json_st = json.dumps(json_dict) # 写入json
        # with open('res.json', 'w', encoding='utf-8') as f:
        #     f.write(json_st)
        return json_dict
    except Exception as e:
        print('get_graph Error', e)


if __name__ == '__main__':
    x = time.time()
    get_graph('user', 'JoveMars')
    print(time.time() - x)