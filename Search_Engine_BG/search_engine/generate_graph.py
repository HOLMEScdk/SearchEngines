# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/4/9 14:26'

from search_engine import DB_Manager
import time
import json

level = ['', 'first', 'second', 'third']


def dfs(url, info_dict, vis, focus):
    '''

    :param url: dfs开始的url
    :param info_dict: 所有url的dict（url: focus_thing）
    :param vis: 是否访问过
    :param focus: 共同的关注内容
    :return: 完成dfs搜索 对focus字典的扩充
    '''
    vis[url] = 1
    url_list = list(info_dict.keys())
    for f_focus in info_dict[url]: # 这个人关注的每个专栏
        for new_url in url_list:
            if not vis[new_url]:  # 没有被访问过的人
                for s_focus in info_dict[new_url]:  # 这个人关注的每个专栏
                    if f_focus == s_focus:
                        focus['focus'].add(f_focus)
                        focus['url'].add(new_url)  # 加入 url
                        focus['url'].add(url)
                        dfs(new_url, info_dict, vis, focus)  # 喜好相同 递归


def get_hobby_circle(url_list):
    info_dict = {}
    for each in url_list:
        cur = DB_Manager.search_mongo('following_columns', each, 'urlToken')
        if cur is None:
            continue
        for temp in cur:
            key, val = temp['urlToken'], [each['title'] for each in temp['following']]
            info_dict[key] = val # combine into a diction
    total_focus = []
    vis = {key: 0 for key in info_dict.keys()}  # init
    for url in info_dict.keys():
        if not vis[url]:
            focus = {'url': set(), 'focus': set()}
            dfs(url, info_dict, vis, focus)
            total_focus.append(focus)
    print(len(total_focus))
    for each in total_focus:
            print(each)


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
        total_token = []
        for each in res:  # 可能输入的名字有多个返回的结果 取一个 es中可能去重复需要假定查找的是关注度多的那个
            each['belong'] = 'root'  # 第一层是root
            json_dict.setdefault(level[1], []).append(each)
            token_list.append(each['urlToken'])
            total_token.append(each['urlToken'])
            break # 防止名字重复 只拿一个

        for i in range(2, 4):  # 每一层的tokenlist用上一次的迭代
            level_res, token_list = DB_Manager.expand_level(kind, token_list)  # 得到新的每一层的结果 结构: [{}, {}]
            if not len(level_res):
                break
            json_dict[level[i]] = level_res
            for each in token_list:  # continuously add into total token  理想情况应当是先不查找.等前端返回请求再查找这玩意
                total_token.append(each)
        get_hobby_circle(total_token)
        # print(json_dict)
        # print(len(json_dict[level[3]]))
        # json_st = json.dumps(json_dict) # 写入json
        # with open('res.json', 'w', encoding='utf-8') as f:
        #     f.write(json_st)
        return json_dict
    except Exception as e:
        print('get_graph Error',e)


if __name__ == '__main__':
    x = time.time()
    get_graph('user', 'JoveMars')
    print(time.time() - x)