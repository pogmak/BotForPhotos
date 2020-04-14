import vk_api
from datetime import datetime, timedelta
import random
import math
import psycopg2
import logging
import os


dbname = 'bot'
dbuser = 'bot'
dbpassword = 'password'

vk_session = vk_api.VkApi('+79991399680', 'makpog9814')
vk_session.auth()

vk = vk_session.get_api()

errorlog = os.path.join('LOG.txt')

#LOGGER
logger = logging.getLogger('VK')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
eh = logging.FileHandler(errorlog)
ch.setLevel(logging.DEBUG)
eh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
eh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(eh)
logger.addHandler(ch)


def loadfromdb():
    result = []
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            query_get = "SELECT photo_id, url, wholikes FROM likes ORDER BY photo_id;"
            cursor.execute(query_get)
            for row in cursor.fetchall():
                result.append(row)
    return result


def loadUsersfromdb():
    result = []
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            query_get = "SELECT chatid,username FROM users;"
            cursor.execute(query_get)
            for row in cursor.fetchall():
                result.append(row)
    return result


def SyncDB():
    photos = []
    ids = []
    for j in range(math.ceil(vk.photos.get(album_id='saved')['count'] / 1000)):
        photos.append(vk.photos.get(album_id='saved', offset=j * 1000, rev=0, count=1000))
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            for saved_photos in photos:
                for items in saved_photos['items']:
                    id = items['id']
                    ids.append(id)
                    url = items['sizes'][-1]['url']
                    #First, check VK id in database, if not exist - add
                    query_find = "SELECT * FROM likes WHERE photo_id={};".format(id)
                    cursor.execute(query_find)
                    if not cursor.fetchall():
                        query_create = "INSERT INTO likes (photo_id,url) VALUES ({},'{}');".format(id,url)
                        cursor.execute(query_create)
                        logger.info("Photo with id={} is not in database, insert...".format(id))
            query_count = "SELECT COUNT(*) FROM likes;"
            cursor.execute(query_count)
            count = cursor.fetchall()[0][0]
            for i in range(0,count):
                query_find = "SELECT photo_id FROM likes WHERE id={};".format(i)
                cursor.execute(query_find)
                id = cursor.fetchall()
                if id:
                    id = id[0][0]
                    if not id in ids:
                        query_delete = "DELETE FROM likes WHERE photo_id={};".format(id)
                        cursor.execute(query_delete)
                        logger.info("Photo with id={} in database, but not in VK, deleted...".format(id))



def updateLikes(photo_id,chatid):
    query_update = "UPDATE likes SET wholikes=array_append(wholikes,{}) WHERE photo_id={};".format(chatid,photo_id)
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            cursor.execute(query_update)


def adduserstodb(chatid,username):
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE chatid='{}';".format(chatid))
            if not cursor.fetchall():
                query_insert = "INSERT INTO users (chatid,username) VALUES ('{}','{}');".format(chatid,username)
                cursor.execute(query_insert)


def addPhotoToDB(id, url):
    with psycopg2.connect(dbname=dbname, user=dbuser, password=dbpassword, host="127.0.0.1", port="5432") as conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO likes (photo_id,url) VALUES ({},'{}');".format(id,url))


def checkLast():
    last = vk.photos.get(album_id='saved', rev=1, count=1)
    for i in last['items']:
        url, id = i['sizes'][-1]['url'], i['id']
        return url, id


if __name__=='__main__':
    pass
