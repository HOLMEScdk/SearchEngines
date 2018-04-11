# -*- coding: utf-8 -*-
# __author__ = 'K_HOLMES_'
# __time__   = '2018/3/20 19:28'


import socket
import general
import DataManager
import HtmlDownload
import time
socket.setdefaulttimeout(general.set_socket_timeout)


def store_focus_list(urlToken, phrase, set_name, total_num):
    cnt = 10
    while cnt > 0:
        cnt -= 1
        flag = False
        try:
            if phrase == 'follower':
                if DataManager.mongo_search_data('follower_info', urlToken) is False:
                    pass
                    flag = HtmlDownload.download_follower(urlToken, 'followers', "follower_info", total_num, 'user')
            elif phrase == 'following':
                if DataManager.mongo_search_data('following_info', urlToken) is False:
                    pass
                    flag = HtmlDownload.download_follower(urlToken, 'following', "following_info", total_num, 'user')
            elif phrase == 'followingColumnsCount':
                flag = HtmlDownload.download_follower(urlToken, 'following/columns', "columns_info", total_num, 'columns')
            elif phrase == 'followingTopicCount':
                flag = HtmlDownload.download_follower(urlToken, 'following/topics', "topics_info", total_num, 'topics')
            if flag is True:
                general.logger.info("%s %s 全部添加进redis中" % (urlToken, phrase) )
                break
        except Exception as e:
            general.logger.warn("%s 获取个人%s列表出现异常 用户%s 剩余次数 %d\n" % (e, phrase, urlToken, cnt))
            time.sleep((10 - cnt) * 2)
    else:  # failed
        DataManager.add_failed_url(set_name, urlToken)



'''
存储个人信息 及 其following/followers
'''
if __name__ == '__main__':
    while True:
        while DataManager.empty_waiting_url(general.waiting_list_url) is True:  # 个人列表未访问存放队列
                time.sleep(general.waiting_time)
                general.logger.warn('Redis 无可爬取个人列表URL 当前进程睡眠\n')
        while not DataManager.empty_waiting_url(general.waiting_list_url):
            print("Working")
            urlToken = DataManager.get_waiting_url(general.waiting_list_url)  # 个人队列
            followerCount = DataManager.get_hash_kv(urlToken, "followerCount")
            followingCount = DataManager.get_hash_kv(urlToken, "followingCount")
            followingTopicCount = DataManager.get_hash_kv(urlToken, "followingTopicCount")
            followingColumnsCount = DataManager.get_hash_kv(urlToken, "followingColumnsCount")
            print(followerCount, followingColumnsCount, followingTopicCount)
            try:
                store_focus_list(urlToken, "follower", general.failed_follower, followerCount)
                store_focus_list(urlToken, "following", general.failed_following, followingCount)
                store_focus_list(urlToken, "followingTopicCount", general.failed_followingtopic, followingTopicCount)
                store_focus_list(urlToken, "followingColumnsCount", general.failed_followingColumns, followingColumnsCount)
                DataManager.delete_hash_kv(urlToken)
                DataManager.add_person_list_success(urlToken)  # 需要清理这个
            except Exception as e:
                print("用户%s列表抓取错误%s"%(urlToken, e))