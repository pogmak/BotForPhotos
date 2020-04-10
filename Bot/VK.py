import vk_api
from datetime import datetime, timedelta
import random
import math
import psycopg2

dbname = 'bot'
dbuser = 'bot'
dbpassword = 'password'

vk_session = vk_api.VkApi('+79991399680', 'makpog9814')
vk_session.auth()

vk = vk_session.get_api()


def loadfromdb():
    result = []
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            query_get = "SELECT photo_id, url, likes_count FROM likes;"
            cursor.execute(query_get)
            for row in cursor.fetchall():
                result.append(row)
    return result

def loadUsersfromdb():
    result = []
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            query_get = "SELECT chatid FROM users;"
            cursor.execute(query_get)
            for row in cursor.fetchall():
                result.append(int(row[0]))
    return result


def createIntoDB():
    photos = []
    for j in range(math.ceil(vk.photos.get(album_id='saved')['count'] / 1000)):
        photos.append(vk.photos.get(album_id='saved', offset=j * 1000, rev=0, count=1000))
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            #Delete table and restart sequence
            cursor.execute("DELETE FROM likes;")
            cursor.execute("ALTER sequence likes_id_seq restart;")
            for saved_photos in photos:
                for items in saved_photos['items']:
                    query_create = "INSERT INTO likes (photo_id,url,likes_count) VALUES ({},'{}',0);".format(items['id'],items['sizes'][-1]['url'])
                    cursor.execute(query_create)


def getByIndex(index):
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            query_count = "SELECT COUNT(*) FROM likes;"
            cursor.execute(query_count)
            count = cursor.fetchall()[0][0]
            query_find = "SELECT url,photo_id FROM likes WHERE id={};".format(count-index)
            cursor.execute(query_find)
            i = cursor.fetchall()
            return i[0][0], i[0][1]
    return None


def getRandom():
    query_count = "SELECT COUNT(*) FROM likes;"
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            cursor.execute(query_count)
            count = cursor.fetchall()[0][0]
            random_id = random.randint(1,count)
            query_find = "SELECT url,photo_id FROM likes WHERE id={};".format(random_id)
            cursor.execute(query_find)
            i = cursor.fetchall()
            return i[0][0], i[0][1]
    return None

def updateLikes(photo_id,likes):
    query_update = "UPDATE likes SET likes_count={} WHERE photo_id={};".format(likes,photo_id)
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            cursor.execute(query_update)
            return True


def getCurrentLikes():
    likes = {}
    query_find = "SELECT photo_id,likes_count FROM likes;"
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            cursor.execute(query_find)
            for i in cursor.fetchall():
                likes[i[0]] = i[1]
            return likes


def adduserstodb(chatid):
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE chatid='{}';".format(chatid))
            if not cursor.fetchall():
            	query_insert = "INSERT INTO users (chatid) VALUES ({});".format(chatid)
            	cursor.execute(query_insert)


def addPhotoToDB(id, url):
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO likes (photo_id,url,likes_count) VALUES ({},'{}',0);".format(id,url))


def checkLast():
    last = vk.photos.get(album_id='saved', rev=1, count=1)
    for i in last['items']:
        url, id = i['sizes'][-1]['url'], i['id']
        return url, id


if __name__=='__main__':
    pass
