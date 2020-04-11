#!/usr/bin/env python
# -*- coding: utf-8 -*-
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
import logging
import VK
import emoji
import random
import os

errorlog = os.path.join('LOG.txt')

logger = logging.getLogger('BOT')
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

TOKEN='1113990897:AAFCbjSkaHIlUgZY8itWm42hErADkpo8dwo'
#REQUEST_KWARGS={
#    'proxy_url': 'socks5://96.96.33.133:1080',
#}


buttons = ['Случайно','Листать последние']

lastest = {}
likes = []
urls = []
users = []
texts_like=['Ржака нах!','Ржака ебать!','Нормальный хуй!', 'Ору!']


def start(update, context):
    chat_id = update.effective_chat.id
    if not chat_id in users:
        users.append(chat_id)
        VK.adduserstodb(chat_id)
        logger.info('Add new user:', str(chat_id))
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
    for l in likes:
        if int(l[0]) == id:
            l[1] += 1
            VK.updateLikes(id, l[1])
            context.bot.send_message(chat_id=chat_id, text=str(l[1]) + emoji.emojize(':thumbs_up:'))
            break
    logger.info('User %s liked photo with id %s' % (chat_id, id))


def send_lastph(update, context):
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
        likes.append([id,0])
        urls.append((id,url))
        likes_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton(random.choice(texts_like) + emoji.emojize(':thumbs_up:'), callback_data=id)]])
        for user in users:
            context.bot.send_message(user,
                             text='Новая сохраненка' + emoji.emojize(':fire::fire::fire:', use_aliases=True))
            context.bot.send_photo(user, photo=url, reply_markup=likes_button)
        VK.addPhotoToDB(id,url)
        logger.info('New photo with id %i has been sent to all users' % id)


def send_toall(update, context):
    message = ' '.join(context.args)
    for user in users:
        context.bot.send_message(user, text=emoji.emojize(message, use_aliases=True))
    logger.info('Message to all has been sent')



if __name__ == '__main__':
    logger.info('Synchronize database with VK. Add new photo and delete deleted')
    VK.SyncDB()
    #Return rows from database (photo_id, url, likes_count)
    rows = VK.loadfromdb()
    for row in rows:
        likes.append([row[0],row[2]])
        urls.append((row[0],row[1]))
    #Переворачиваем, потому как фотографии с конца будет быстрее искать
    likes.reverse()

    logger.info('Loading users form database')
    users = VK.loadUsersfromdb()
    logger.info('Database succesefull load')

    updater = Updater(TOKEN, use_context=True)
    job = updater.job_queue
    job.run_repeating(callback=newSavedUpdater,interval=60)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('secrettoall', send_toall))
    dispatcher.add_handler(MessageHandler(Filters.text(buttons), HandlerButtons))
    dispatcher.add_handler(CallbackQueryHandler(like))
    updater.start_polling(timeout=123)

