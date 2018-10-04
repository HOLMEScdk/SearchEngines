# Final Presentation 
 ### 1.  Architecture Overview 
![1](https://github.com/HOLMEScdk/SearchEngines/raw/master/img/1.png)
### 2.  Basic Distributed Structure
![2](https://github.com/HOLMEScdk/SearchEngines/raw/master/img/2.png)
### 3. Ranking
![3](https://github.com/HOLMEScdk/SearchEngines/raw/master/img/3.png)
### 4. Figure Relationship Diagram
 ![4](https://github.com/HOLMEScdk/SearchEngines/raw/master/img/4.png)
### 5. Search Function
![6](https://github.com/HOLMEScdk/SearchEngines/raw/master/img/6.png)
![8](https://github.com/HOLMEScdk/SearchEngines/raw/master/img/8.png)
### 6. Database 

![7](https://github.com/HOLMEScdk/SearchEngines/raw/master/img/7.png)


# SearchEngines




Contains Crawler，Indexing，  Word Segmentation，Distributed System 





*** 
**已更新** 2018/3/26
# 爬虫部分
## 主题： 知乎个人用户信息抓取
### 基本信息

参考界面信息：https://www.zhihu.com/people/gashero/answers
工具及环境： Redis + MongoDB + Anaconda （最新版)
需要知识： 基本网页知识，线程通信，爬虫及反爬虫（我也就看了两天书就xjb上了），数据库，一丢丢数据结构，正则表达式，进程线程（操作系统上的概念实现），字符编码格式（虽然python3都是unicode 但是还是遇到了莫名其妙的问题在用上述东西的时候）

一些包  Pymongo redis urllib BeautifulSoup
* **general.py**为全局初始化 参数的设置 
* **Open_Proxy_.py** 为更换代理池 已完成 使用的代理池为开源地址：https://github.com/qiyeboy/IPProxyPool
* **Crawler_Start.py** 对于个人的用户的基本信息的爬取
* **Crawler_Start_List.py** 对于个人用户的follower/following信息的爬取
* **DataManager.py** 管理MongoDB以及Redis,及增删改操作的接口
* **HtmlDownload.py** 获取知乎的页面信息并解析,一部分作为*start.py*的接口 一部分作为*start_list.py*的接口
* Crawler_Main.py 原本是开始跑这个玩意的（更改方案之后已废弃）
* Crawler.Init.py （已废弃）

###  讲解流程之前务必提及的一些坑
* 到底sleep()多久以及在哪个位置上设置等待点是Key Point，有可能睡的位置、时长不对都会导致被反爬虫发现，常见就是429 或者 直接就gg
* 到底是使用 多线程 还是 多进程呢？ 首先，我使用的是Python，python在多进程的底层实现上是能做到并行的（进程数在cpu以内），但是由于GIL(有点不确定)的存在，在多线程的实现上其实并没有并行（有误请发issue）。因此，对python来说，多进程是针对cpu计算密集型的，而多线程是针对io等待密集型任务的，因此到底自己要使用哪个都需要自己提做好架构分析，然后再根据实际的测试集进行验证，选择。
* 代理IP池，有一个较好的分配ip的方案实现，处理好每个ip的使用频率

### 大致思路
#### 数据库及分布式
    数据库选用MongoDB存储，量大，易完成高效读写
    Redis使用为了实现缓存，将每个用户的urlToken作为唯一key存入set达到Hash效果，这样在内存中的效率比访问MongoDB去重快很多。
        1. redis除了存储url去重之外，还做了一些其他滤检测的工作，如，访问成功的url（个人用户）应当放到成功的集合中，并且有一个zset存储的是用户的url以及他的follower。（这一点是为了之后做一些基本工作的时候可以知道哪些是大V，follower大的即大v）
        2. 失败队列的添加，一些用户可能设置了非登录用户不可见的功能，则一般信息访问不到，（未做登录功能）因此可以将此类用户以及一些访问失败(429)的用户加入到失败队列中
        3. 将代理的ip也
    分布式上MongoDB采用简单的集群备份，Redis大概算了下就算有上亿数据，几个字节一个urltoken好像才几百MB，目前先不做集群。
    
    爬虫的时候选用主从模式，因为这个简单好做，只要一台主机发布url信息，从机去redis中获得url，并加以多进程/线程，可以达到需求。
    
    目前针对实际的代码来说其实可以每台机器都跑，他们一齐处理redis中的等待对立的信息，因为redis自己实现了同步的机制，所以并不会发生问题，但是存入数据库的读写的时候还没有查证相关资料是否会造成问题，但是由于选取的用户信息是不同的(则写入信息也是不一样的)并不会造成数据集的冲突。


### 知乎用户信息
这个。。内容就很多了，他们的前端信息需要详细分析过，我大概花了3h从页面中获得了json的数据，但是抄录下来并对照真正的显示在页面上的信息还是要花费很长的时间。以下列部分
#### Following 的信息
* topics (话题)
* columns(专栏)
* following(关注人数)
* 舍去了可以爬取的收藏夹以及问题，因为前者提供的信息不多用处不大，后者数据量太大，无疑又增大资源消耗，有条件的可以在我的代码上增加(很方便，我提供的都是接口)
#### Follower的信息摘要
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

以上 等有进一步的数据分析结果之后再做更新。
