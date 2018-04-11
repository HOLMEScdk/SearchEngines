# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/4/6 13:27'

import DataManager
import HtmlDownload
import time
import jieba
htmldownd = HtmlDownload.HtmlDownload()
'''
需要更新用户的个人信息 然后是用话题的关注数量
传入更新的表，然后返回对应urltoken的信息，然后去重新爬取更新字段
'''


def add_missing_part(table):
#  topics新增followers 和 questions
    missing_part = dict()
    if table == 'topics_info':
        res = DataManager.get_table(table)
        cnt = 0
        with open('topic_url.txt', 'a+', encoding='utf-8') as f1, open('topic_name.txt', 'a+', encoding='utf-8') as f2:
            for v in res:
                # print(v['info']['name'])
                f1.write(v['urlToken'] + ' 4\n')
                f2.write(v['info']['name'] + ' 4\n')
                # jieba.add_word(v['info']['name'])
                data = htmldownd.download(v['urlToken'], 'topic', 'topic')
                data = data['entities']['topics']
                if data.get(v['urlToken']) is None:
                    continue
                missing_part[v['urlToken']] = {'urlToken': v['urlToken'], 'questions': data[v['urlToken']]['unansweredCount'],
                                               'followers': data[v['urlToken']]['followersCount']}
                cnt += 1
                if cnt % 1000 == 0:
                    DataManager.add_missing_part(table, missing_part)
                    print("%d" % cnt)
        # for each in missing_part:
        #     print(missing_part[each])
    elif table == 'person_table':
        res = DataManager.get_table(table)
        cnt = 0
        with open('dict_url.txt', 'a+', encoding='utf-8') as f1, open('dict_name.txt', 'a+', encoding='utf-8') as f2:
            for each in res:
                cur_name = DataManager.find_json(each['urlToken'])
                # # add jieba
                # jieba.add_word(cur_name)
                # jieba.add_word(each['urlToken'])
                s1 = each['urlToken'] + ' 4\n'
                s2 = cur_name + ' 4\n'
                f1.write(s1)
                f2.write(s2)
                cnt += 1
                if cnt % 1000 == 0:
                    print("%d"% cnt)


if __name__ == '__main__':
    while True:
        #add_missing_part("topics_info")
        add_missing_part("person_table")
        time.sleep(60)
