#!/usr/bin/env python
# -*- coding: utf-8 -*-
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, JobQueue
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, error, message
import logging
import VK
import emoji
import random
import time

from datetime import datetime

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

TOKEN='1113990897:AAFCbjSkaHIlUgZY8itWm42hErADkpo8dwo'
#REQUEST_KWARGS={
#    'proxy_url': 'socks5://96.96.33.133:1080',
#}


buttons = ['Случайно','Листать последние']

lastest = {}
likes = {}
urls = []
users = []
texts_like=['Ржака нах!','Ржака ебать!','Нормальный хуй!']


def start(update, context):
    chat_id = update.effective_chat.id    
    if not chat_id in users:    
        users.append(chat_id)
        VK.adduserstodb(chat_id)
        logging.info('Add new user:', str(chat_id))

    lastest[chat_id] = -1
    menu = ReplyKeyboardMarkup.from_row(buttons)
    wait_job = context.job_queue.run_repeating(newSavedUpdater,10,context=chat_id)
    Hello_message = """Привет! Я бот для сохраненок Макара. Бот будет присылать тебе новые сохраненки, а также
    ты можешь полистать их самостоятельно, используя кнопки."""
    context.bot.send_message(chat_id=chat_id,text=Hello_message, reply_markup=menu)


def like(update, context):
    global likes
    chat_id = update.effective_chat.id
    query = update.callback_query
    query.answer()
    query.edit_message_reply_markup(reply_markup=None)
    id = int(query.data)
    likes[id] += 1
    VK.updateLikes(id, likes[id])
    context.bot.send_message(chat_id=chat_id,text=str(likes[id])+emoji.emojize(':thumbs_up:'))
    logging.info('User %s liked photo with id %s' % (chat_id, id))    


def send_lastph(update, context):
    global likes
    chat_id = update.effective_chat.id
    if not chat_id in lastest:
        lastest[chat_id] = -1
    url = urls[lastest[chat_id]][1]
    id = urls[lastest[chat_id]][0]
    likes_button = InlineKeyboardMarkup([[InlineKeyboardButton(random.choice(texts_like)+emoji.emojize(':thumbs_up:'), callback_data=id)]])
    context.bot.send_photo(chat_id=chat_id, photo=url,reply_markup=likes_button)
    lastest[chat_id] -= 1


def send_randph(update, context):
    chat_id = update.effective_chat.id
    index = random.randint(0,len(urls))
    id = urls[index][0]
    url = urls[index][1]
    likes_button = InlineKeyboardMarkup([[InlineKeyboardButton(random.choice(texts_like) + emoji.emojize(':thumbs_up:'), callback_data=id)]])
    context.bot.send_photo(chat_id=chat_id, photo=url,reply_markup=likes_button)


def HandlerButtons(update, context):
    chat_id = update.effective_chat.id
    if update.message.text == buttons[0]:
        send_randph(update, context)
    elif update.message.text == buttons[1]:
        send_lastph(update, context)


def newSavedUpdater(context):
    url, id = VK.checkLast()
    ids = [x[0] for x in urls]
    if not id in ids:
        likes[id] = 0
        urls.append((id,url))
        likes_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton(random.choice(texts_like) + emoji.emojize(':thumbs_up:'), callback_data=id)]])
        for user in users:
            context.bot.send_message(user,
                             text='Новая сохраненка' + emoji.emojize(':fire::fire::fire:', use_aliases=True))
            context.bot.send_photo(user, photo=url, reply_markup=likes_button)
        VK.addPhotoToDB(id,url)
        logging.info('New photo with id %i has been sent to all users' % id)

if __name__ == '__main__':
    logging.info('Loading likes and urls from current database')

    #Return rows from database (photo_id, url, likes_count)
    rows = VK.loadfromdb()
    if rows:
        for row in rows:
            likes[row[0]] = row[2]
            urls.append((row[0],row[1])) 
    else:
        logging.info('Database is empty. Dont read.')
    logging.info('Loading users form database')
    users = VK.loadUsersfromdb()
    logging.info('Clear database and load new data')
    VK.createIntoDB()
    if not rows:  
        for row in VK.loadfromdb():
            likes[row[0]] = row[2]
            urls.append((row[0],row[1])) 

    logging.info('Database succesefull load')
    updater = Updater(TOKEN, use_context=True)
    job = updater.job_queue
    job.run_repeating(callback=newSavedUpdater,interval=10)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(MessageHandler(Filters.text(buttons), HandlerButtons))
    dispatcher.add_handler(CallbackQueryHandler(like))

    updater.start_polling(timeout=30, read_latency=10)
