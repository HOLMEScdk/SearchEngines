# SearchEngines
Contains Crawler，Indexing，  Word Segmentation，Distributed System 

# 爬虫部分
## 主题： 知乎个人用户信息抓取
### 基本信息
参考界面信息：https://www.zhihu.com/people/gashero/answers
工具及环境： Redis + MongoDB + Anaconda （最新版)
需要知识： 基本网页知识，线程通信，爬虫及反爬虫（我也就看了两天书就xjb上了），数据库，一丢丢数据结构，字符编码格式（虽然python3都是unicode 但是还是遇到了莫名其妙的问题在用上述东西的时候）

一些包  Pymongo redis urllib BeautifulSoup
* general.py 为全局初始化
* Crawler_Main.py 当然是开始跑这个玩意的
* Crawler.Init.py 为更换代理池 目前还未写完 使用的代理池为开源 地址：https://github.com/qiyeboy/IPProxyPool
* Crawler_Start.py 为爬虫爬取内容并存入数据库的操作
* DataManager.py 管理MongoDB以及Redis
* HtmlDownload.py 获取知乎的页面信息并解析

### 大致思路
#### 数据库及分布式
* 数据库选用MongoDB存储，量大，易完成高效读写
* Redis使用为了实现缓存，将每个用户的urlToken作为唯一key存入set达到Hash效果，这样在内存中的效率比访问MongoDB去重快很多。（还有很多用到了Redis，写完再补）
* 分布式上MongoDB采用简单的集群备份，Redis大概算了下就算有上亿数据，几个字节一个urltoken好像才几百MB，目前先不做集群。爬虫的时候选用主从模式，因为这个简单好做，只要一台主机发布url信息，从机去redis中获得url，并加以多线程，可以达到需求
**现在单机上发现了重要的一点，没先分段存储，这样一下子存个轮子的数据，几十万，数组内存也难受了**

### 知乎用户信息
这个。。内容就很多了，他们的前端信息需要详细分析过，我大概花了3h从页面中获得了json的数据，但是抄录下来并对照真正的显示在页面上的信息还是要花费很长的时间。以下列部分
!!! 写的时候都要注意数组大小
user['badge'][0] # 获得个人成就内容
user['badge'][0]['description'] # 优秀话题回答者称号
user['badge'][0]['topics'][0]['name'] #各称号的名字（先获得size）
如果没有称号则badge大小为0 
```python
# 有删减 列出部分
s = BS(html, 'lxml')
data = s.find('div', attrs={'id':'data'})['data-state']
data = json.loads(data)
# 用户的headline 
user['headline']
# 个人简介
user['description'] 
# 教育经历
user['educations'] 
user['educations'][0]['major']['name'] 
user['educations'][0]['school']['name']
# 职业经历
user['employments'][0]['company']['name']
user['employments'][0]['job']['name']
# 所在行业
user['business']['name'] #有些人没有这个business
# 文章被收藏数
user['favoritedCount']
# 回答数量
user['answerCount']
# 提问数
user['questionCount']
# 文章数
user['articlesCount']
# 专栏数 
user['columnsCount']

# 粉丝
user['followerCount']
#关注的专栏数
user['followingColumnsCount']
# 他关注的个数
user['followingCount']
# 关注的收藏夹
user['followingFavlistsCount']
# 关注的问题
user['followingQuestionCount']
# 关注话题
user['followingTopicCount']
# 举办的live
user['hostedLiveCount']
# 参加的live
user['participatedLiveCount']
# 居住地
user['locations'][0]['name']
# 参与公共编辑数
user['logsCount']
# 获得点赞数
user['voteupCount']
# 感谢数
user['thankedCount']
# 是否是人物
#user['type'] == 'people'
user['gender'] # -1 无性别 0 woman 1 man
#-------------------------------------------------------------------
'''
data['entities'] 下有15个内容
users
questions
answers
articles
columns
topics
roundtables
favlists
comments
notifications
ebooks
activities
feeds
pins
promotions
''' 换url
#关注他的人提取新用户的id 可获得新url # 这个只针对第一页 后面内容需要修改
 for each in data['entities']['user']['gashero']['ids']:
    if each is not None:
        print(each)
# 他关注的人
 for each in data['people']['followingByUser']['gashero']['ids']:
  if each is not None:
      print(each)
```

以上 先BB这么点 时间没多少