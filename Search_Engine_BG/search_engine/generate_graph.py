# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/4/9 14:26'

from search_engine import DB_Manager
import time
import json

level = ['', 'first', 'second', 'third']


def dfs(url, info_dict, vis, focus):
    '''
    判断有无关联的专栏交集
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
        # cur = DB_Manager.search_mongo('following_columns', each, 'urlToken')
        cur = DB_Manager.search_es('following_columns', each, 'urlToken_col')
        if cur is None:
            continue
        # print(cur.count())
        for temp in cur:
            temp = temp['_source']
            print(temp)
            key, val = temp['urlToken_col'], [each['title'] for each in temp['following_col']]  # 每个人喜欢的专栏 及 当然人的key
            # key, val = temp['urlToken'], [each['title'] for each in temp['following']]
            info_dict[key] = val  # combine into a diction
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

    :param kind:  类型 person topic column
    :param name: 查找名字
    :param urlToken: id
    :return: 关系字典
    '''
    try:
        if urlToken is None and name is not None:
            res = DB_Manager.find_database(kind, name, 'name')  # 去es检索
        else:
            if kind == 'person':
                db_name = 'person_table'
            elif kind == 'topic':
                db_name = 'topics_info'
            else:
                 db_name = 'columns_info'
            res = DB_Manager.search_mongo(db_name, urlToken, '_id')
            # print(db_name, urlToken, "--------------")
        if res is None:
            return None
        json_dict = {}
        token_list = []
        total_token = []
        # print("FIRST: ", res[0])
        for each in res:  # 可能输入的名字有多个返回的结果 取一个 es中可能去重复需要假定查找的是关注度多的那个
            if urlToken is not None:
                temp = each
                temp['id'] = str(each['_id'])
                temp.pop('_id')
                # print(temp)
            else:
                temp = each['_source']
                temp['id'] = each['_id']
                # print(temp['id'])
            temp['belong'] = 'root'  # 第一层是root
            json_dict.setdefault(level[1], []).append(temp)
            token_list.append(temp['urlToken'])
            total_token.append(temp['urlToken'])
            break  # 防止名字重复 只拿一个
        for i in range(2, 4):  # 每一层的tokenlist用上一次的迭代
            # print(i)
            level_res, token_list = DB_Manager.expand_level(kind, token_list)  # 得到新的每一层的结果 结构: [{}, {}]
            if not len(level_res):
                break
            json_dict[level[i]] = level_res
            # print(level_res)
            for each in token_list:  # continuously add into total token  理想情况应当是先不查找.等前端返回请求再查找这玩意
                total_token.append(each)
        # print(total_token)
        # print(len(total_token))
        t1 = time.time()
        # get_hobby_circle(total_token)
        # print(time.time() - t1)
        # print(json_dict)
        # json_st = json.dumps(json_dict) # 写入json
        # with open('topic.json', 'w', encoding='utf-8') as f:
        #     f.write(json.dumps())
        return json_dict
    except Exception as e:
        print('get_graph Error'+e)


if __name__ == '__main__':
    x = time.time()
    # get_graph('user', 'JoveMars')
    # re = DB_Manager.search_mongo('person_table', '5ab9f746fbb12069b43f28ee', '_id')
    re = DB_Manager.search_mongo('top_persons')
    # re = DB_Manager.search_es('person_table', 'excited-vczh', 'urlToken')
    print(re)
    print(time.time() - x)