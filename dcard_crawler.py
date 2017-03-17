# coding: utf-8
import uuid
import requests
from time import sleep
from pymongo import MongoClient
client = MongoClient()
db = client.dcard


# forum_url = 'https://www.dcard.tw/_api/forums/' + forum_name + '/posts?before= post_id'
# post_url = 'https://www.dcard.tw/_api/posts/' + post_id
# comment_url = 'https://www.dcard.tw/_api/posts/'+ post_id + '/comments?after=60'

forum_name_list = ['talk', 'acg', 'game', 'pokemon', 'movie', 'photography', '3c', 'job', 'music', 'sport', 'travel', 'book', 'studyabroad', 'literature', 'exam', 'course', 'sex', 'dcard', 'whysoserious']
#forum_name_list = ['vehicle', 'language', 'relationship', 'girl', 'makeup', 'dressup', 'funny', 'rainbow', 'marvel', 'boy', 'horoscopes', 'food', 'mood', 'pet', 'handicrafts', 'trending', 'talk', 'acg', 'game', 'pokemon', 'movie', 'photography', '3c', 'job', 'music', 'sport', 'travel', 'book', 'studyabroad', 'literature', 'exam', 'course', 'sex', 'dcard', 'whysoserious']
# board_name = ['汽機車', '語言', '感情', '女孩', '美妝', '穿搭', '有趣', '彩虹', '靈異', '男孩', '星座', '美食', '心情', '寵物', '手作', '時事', '閒聊', '動漫', '遊戲', '寶可夢', '影劇', '攝影', '3C', '工作', '音樂', '運動', '旅遊', '書籍', '留學', '詩文', '考試', '課程', '西斯', 'Dcard', '廢文']


def crawl_posts_list(forum_name, last_post_id=None):
    print("crawling forum_name: " + forum_name)
    forum_url = 'https://www.dcard.tw/_api/forums/' + forum_name + '/posts'
    if last_post_id != None:
        print("crawling forum_name: " + forum_name + " before = " + str(last_post_id))
        forum_url = 'https://www.dcard.tw/_api/forums/' + forum_name + '/posts?before=' + str(last_post_id)
    res = crawler(forum_url)
    print("post length: " + str(len(res)))
    return res


def crawl_post(post_id):
    print("crawling post: " + str(post_id))
    post_url = 'https://www.dcard.tw/_api/posts/' + str(post_id)
    res = crawler(post_url)
    return res


def crawl_comment(post_id, lase_comment_count = None):
    print("crawling comment: "+ str(post_id))
    comment_url = 'https://www.dcard.tw/_api/posts/'+ str(post_id) +'/comments?after=' + str(lase_comment_count)
    res = crawler(comment_url)
    print("comment length: "+ str(len(res)))
    return res
 

def change_id_to_mongodb_format(data_list):
    if type(data_list) == dict:
        data_list = [data_list]
    for data in data_list:
        try:
            data['_id'] = data['id']
            data.pop('id', None)
        except Exception as e:
            data['_id'] = uuid.uuid4()
            print(data)
            print(repr(e))
    return data_list


# In[12]:

def crawler(url):
    res = requests.get(url)
    res.encoding = 'utf-8'
    if res.status_code is 200:
        if res is None:
            print("Response is Null" + url)
            return []
        else:
            try:
                return res.json()
            except Exception as e:
                print(res.text + " : " + str(e))
                return []
    else:
        print(res.status_code)
        print("Sleep one minutes.")
        sleep(60)
        return crawler(url)


def insert_to_mongodb(collection_name, data_list):
    if len(data_list) > 0 :
        for data in data_list:
            db[collection_name].update_one({'_id':data['_id']}, {'$set': data}, True)
        return
    else:
        return


# In[ ]:

for forum_name in forum_name_list:
    last_post_id = None
    while True:
        # Every length of posts_list will be 30.
        posts_list = crawl_posts_list(forum_name, last_post_id=last_post_id)
        if len(posts_list) == 0:
            print("Finish forum_name crawling!")
            break
        for index, post in enumerate(posts_list):
            post_id = post['id']
            # To crawl post.
            insert_to_mongodb(forum_name + '_posts', change_id_to_mongodb_format(crawl_post(post_id)))

            # To crawl all of the comments from post.
            if post['commentCount'] <= 30:
                comment_data = crawl_comment(post_id, 0)
                insert_to_mongodb(forum_name + '_comments', change_id_to_mongodb_format(comment_data))
            else:
                last_comment_count = 0
                while True:
                    comment_data = crawl_comment(post_id, last_comment_count)
                    if len(comment_data) == 0:
                        break
                    insert_to_mongodb(forum_name + '_comments', change_id_to_mongodb_format(comment_data))
                    last_comment_count += 30
            # To crawl next 30 posts
            if index == len(posts_list)-1:
                print("Crawl next 30 posts!")
                last_post_id = post_id


# todo 把每一篇論壇文章 拿去做LDA 可以找出subtitle. 
# todo 可以用query 把撈出的文章 做LDA 看準不準
