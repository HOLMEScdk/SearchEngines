from django.shortcuts import render
from django.shortcuts import HttpResponse

# Create your views here.
from search_engine import generate_graph, Rules, generate_rank, fulltext_retrieval, update_info, DB_Manager
import jieba
import re
import json
import time
import random
jieba.load_userdict('data1_dict.txt')


def init(request):
    return render(request, 'index1.html')


def search(request):
    res_dict = dict()
    if request.method == 'GET':
        start_time = time.time()
        text = request.GET.get('test')  # input name
        if type(text) is None:
            print('None')
            HttpResponse(json.dumps({'NONE': True}))
        cut = jieba.cut_for_search(text)
        joint_cut = ','.join(cut)
        list_text = [x for x in re.split(r'[\s!@%^,;\n]', joint_cut) if x]  # divide word
        print(list_text)
        flag, name, kind = Rules.judge_rule(list_text)  # 划分
        print(flag, name, kind)
        if flag == 0:  # 全文检索
            res_dict = fulltext_retrieval.retrieval(text)
        if flag == 1:  # 层次图
            res_dict = generate_graph.get_graph('person', name)
        elif flag == 2:  # Rank
            number_list = re.findall(r"\d+\.?\d*", text)  # 正则提取数字
            if len(number_list) == 0: # 默认排名前10名
                number_list.append(10)
            else:
                number_list = list(map(int, number_list))
                number_list = sorted(number_list)[:2]
            # 硬编码解析语义
            table_name, key, search_dict = generate_rank.analyze_meaning(text, number_list)
            # print(table_name, key, search_dict)
            res_dict = generate_rank.get_rank(table_name, key, search_dict)
        elif flag == 3:
            pass
        end_time = time.time()
        if res_dict is None:
            return HttpResponse(json.dumps({'NONE': True}))
        res_dict['total_time'] = end_time - start_time
        res_dict['type'] = kind if kind is not None else "list"
        # print(res_dict)
        # with open('show_list.json', 'w', encoding='utf-8') as f:
        #     f.write(json.dumps(res_dict))
    return HttpResponse(json.dumps(res_dict))


def relation(request):
    res_dict = {'NONE': True}
    if request.method == 'GET':
        start_time = time.time()
        text_id = request.GET.get('id')  # get id
        res_dict = generate_graph.get_graph('person', None, text_id)  # 传入id
        # print(text_id)
        if res_dict is None:
            return HttpResponse(json.dumps({'NONE': True}))
        end_time = time.time()
        res_dict['total_time'] = end_time - start_time
        res_dict['type'] = 'user'
        # print("Relation", res_dict)
    return HttpResponse(json.dumps(res_dict))


def update(request):
    res_dict = {'NONE': True}
    if request.method == 'GET':
        id = request.GET.get('id')
        urlToken = request.GET.get('token')
        res_dict = update_info.udpate_person(id, urlToken)
    res_dict['id'] = str(res_dict['_id'])
    res_dict.pop('_id')
    # print(res_dict)
    return HttpResponse(json.dumps(res_dict))


def change(request):
    res_dict = {'NONE': True}
    if request.method == 'POST':
        start_time = time.time()
        parameter_dict = request.POST.dict()
        parameter_dict['range'] = []
        if parameter_dict.get('score1') is not None:
            parameter_dict['range'].append(int(parameter_dict['score1']))
        if parameter_dict.get('score2') is not None:
            parameter_dict['range'].append(int(parameter_dict['score2']))
        parameter_dict['total'] = int(parameter_dict['total'])
        parameter_dict.pop('range[]')
        # print(parameter_dict)
        # parameter_dict = {'type':'score', 'table_name': 'person_table', 'search_key': 'voteupCount',
        #                   'count': 'voteupCount', 'range': [3000, 5000], 'status': '上',
        #                   'total': 7287, 'meaning': '点赞数'}
        res_dict = generate_rank.get_another_rank(parameter_dict)
        res_dict['total_time'] = time.time() - start_time
        string = parameter_dict['table_name']
        if 'person' in string:
            key = 'user'
        elif 'column' in string:
            key = 'column'
        else:
            key = 'topic'
        res_dict['type'] = key
        # print(res_dict)
        # with open('another_change.json', 'w', encoding='utf-8') as f:
        #     f.write(json.dumps(res_dict))
    return HttpResponse(json.dumps(res_dict))


def getlist(request):
    res_dict = {'NONE': True}
    if request.method == 'GET':
        t1 = time.time()
        # val, type(person), key
        val = request.GET.get('id')
        type_ = request.GET.get('type')
        key = request.GET.get('data')
        res = []
        table_name, search_table = "", ""
        current_type = 'es'
        if type_ == 'person':
            if 'columns' in key or 'Column' in key:
                table_name = 'following_columns'
                search_table = 'columns_info'
            elif 'topic' in key or 'Topic' in key:
                table_name = 'following_topics'
                search_table = 'topics_info'
            elif 'followerCount' in key:
                table_name = 'follower_info'
                search_table = 'person_table'
            else:
                table_name = 'following_info'
                search_table = 'person_table'
            search_key = 'urlToken_col' if table_name == 'following_columns' else 'urlToken'
            # print(table_name, val, search_key, search_table)
            res = DB_Manager.search_es(table_name, val, search_key, 1)
            if res is None:
                current_type = 'mongo'
                res = DB_Manager.search_mongo(table_name, val, "urlToken")
        # elif type_ == 'column':
        #     table_name = 'columns_info'
        #     res = DB_Manager.search_es(table_name, val, 'urlToken', 1)
        # else:  # 话题
        #     table_name = 'topics_info'
        #     res = DB_Manager.search_es(table_name, val, 'urlToken', 1)
        if res is None:
            print("NONE HERE")
            return HttpResponse(json.dumps(res_dict))
        if table_name == 'following_columns':
            special_key = 'following_col' if current_type == 'es' else 'following'
        elif table_name == 'following_topics' or table_name == 'following_info':
            special_key = 'following'
        else:
            special_key = 'followers'

        res_dict = {"result": []}
        temp = dict()

        for each in res:  # 拿找到的第一个 无论是es 还是 mongo
            temp = each['_source'] if current_type == 'es' else each
            temp['id'] = str(each['_id'])
            if temp.get('_id') is not None:
                temp.pop('_id')
            break
            # print(temp)
        temp_list = []
        random_list = []
        if 'columns' in search_table or 'topics' in search_table:
            for each in temp[special_key]:
                random_list.append(each['urlToken'])
        else:
            random_list = list(temp[special_key])
        print(random_list)
        random_list_size = len(random_list)
        s_set = set()
        if random_list_size > 10:
            while len(s_set) < 10:
                s_set.add(random.randint(0, random_list_size-1))
        else:
            s_set = {i for i in range(random_list_size)}
        for each in s_set:  # 随机的下标
            # print(search_table, random_list[each])
            current_person_info = DB_Manager.search_es(search_table, random_list[each], 'urlToken', 1)
            if current_person_info is not None:
                for now in current_person_info:  # es 只检索一个
                    if search_table == 'person_table':
                        temp_list.append({"name": now['_source']['name'],
                                          "photo_url": DB_Manager.change_photo_url(now['_source']['photo_url'], 'person')})
                    elif search_table == 'columns_info':
                        temp_list.append({"name": now['_source']['info']['title'], "photo_url":
                            DB_Manager.change_photo_url(now['_source']['info']['photo_url'], 'columns')})
                    else:
                        temp_list.append({"name": now['_source']['info']['name'], "photo_url":
                            DB_Manager.change_photo_url(now['_source']['info']['avatarUrl'], 'topics')})

        # print(temp[special_key])
        temp[special_key].clear()
        temp["followers"] = temp_list
        res_dict['result'].append(temp)
        res_dict['total_time'] = time.time() - t1
        # print(res_dict)
        # print(id, type_, key)
    return HttpResponse(json.dumps(res_dict))


