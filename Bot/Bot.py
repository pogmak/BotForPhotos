#!/usr/bin/env python
# -*- coding: utf-8 -*-
from telegram.utils.promise import Promise
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, MessageQueue
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Bot
import logging
import VK
from emoji import emojize
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

vk_id = '255798202'
TOKEN='1113990897:AAFCbjSkaHIlUgZY8itWm42hErADkpo8dwo'

#REQUEST_KWARGS={
#    'proxy_url': 'socks5://96.96.33.133:1080',
#}


buttons = ['Случайно','Листать последние']

lastest = {}
likes = {}
urls = []
users = {}
texts_like=['Ржака нах!','Ржака ебать!','Нормальный хуй!', 'Ору!']


def GetLikeButton(photo_id):
    vk_url = 'https://vk.com/photo%s_%s' % (vk_id,photo_id)
    layout = [
        [InlineKeyboardButton(random.choice(texts_like) + emojize(':thumbs_up:'), callback_data=photo_id),
         InlineKeyboardButton(text='VK',url=vk_url)]
    ]
    return InlineKeyboardMarkup(layout)


def GetAnotherButtons(photo_id):
    vk_url = 'https://vk.com/photo%s_%s' % (vk_id,photo_id)
    callback = 'who|%s' % photo_id
    layout = [
        [InlineKeyboardButton(text=str(len(likes[photo_id])) + emojize(':thumbs_up:'),callback_data=callback),
         InlineKeyboardButton(text='VK',url=vk_url)]
    ]
    return InlineKeyboardMarkup(layout)


class MQBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._message_queue = MessageQueue(
            all_burst_limit=30,
            all_time_limit_ms=1000
        )

    def __del__(self):
        try:
            self._message_queue.stop()
        finally:
            super().__del__()

    def send_message(self, *args, **kwargs):
        is_group = kwargs.get('chat_id', 0) >= 0
        return self._message_queue(Promise(super().send_message, args, kwargs), is_group)


def start(update, context):
    chat_id = update.effective_chat.id
    if not chat_id in list(users.keys()):
        username = update.effective_chat.username
        welcome_text = "Приветствуем нового сюсюкена:" + username + emojize(':green_heart:')
        for user in list(users.keys()):
            context.bot.send_message(chat_id=user, text=welcome_text)
        users[chat_id] = username
        VK.adduserstodb(chat_id,username)
        logger.info('Add new user:%s %s' % (chat_id,username))
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
    data = query.data
    if data.split('|')[0] == 'who':
        id = int(data.split('|')[1])
        message = "WHO LIKES:\n"+'\n'.join(users[x] for x in likes[id])
        query.answer(text=message, show_alert=True)
    else:
        query.answer()
        id = int(data)
        likes[id].append(chat_id)
        VK.updateLikes(id, chat_id)
        query.edit_message_reply_markup(reply_markup=GetAnotherButtons(id))
        logger.info('User %s liked photo with id %s' % (chat_id, id))


def send_lastph(update, context):
    chat_id = update.effective_chat.id
    if not chat_id in lastest:
        lastest[chat_id] = -1
    url = urls[lastest[chat_id]][1]
    id = urls[lastest[chat_id]][0]
    if chat_id in likes[id]:
        button = GetAnotherButtons(id)
    else:
        button = GetLikeButton(id)
    context.bot.send_photo(chat_id=chat_id, photo=url,reply_markup=button)
    lastest[chat_id] -= 1


def send_randph(update, context):
    chat_id = update.effective_chat.id
    index = random.randint(0,len(urls))
    id = urls[index][0]
    url = urls[index][1]
    if chat_id in likes[id]:
        button = GetAnotherButtons(id)
    else:
        button = GetLikeButton(id)
    context.bot.send_photo(chat_id=chat_id, photo=url,reply_markup=button)


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
        likes[id] = []
        urls.append((id,url))
        likes_button = InlineKeyboardMarkup(GetLikeButton(id))
        for user in list(users.keys()):
            context.bot.send_message(user,text='Новая сохраненка %s' % emojize(':fire::fire::fire:', use_aliases=True))
            context.bot.send_photo(user, photo=url, reply_markup=likes_button)
        VK.addPhotoToDB(id,url)
        logger.info('New photo with id %i has been sent to all users' % id)


def send_toall(update, context):
    message = ' '.join(context.args)
    for user in list(users.keys()):
        context.bot.send_message(user, text=emojize(message, use_aliases=True))
    logger.info('Message to all has been sent')



if __name__ == '__main__':
    bot = MQBot(token=TOKEN)
    logger.info('Synchronize database with VK. Add new photo and delete deleted')
    VK.SyncDB()
    #Return rows from database (photo_id, url, likes_count)
    rows = VK.loadfromdb()
    for row in rows:
        if row[2] == None:
            likes[row[0]] = []
        else:
            likes[row[0]] = row[2]
        urls.append((row[0],row[1]))

    logger.info('Loading users form database')
    rows = VK.loadUsersfromdb()
    for row in rows:
        if row[1]:
            users[int(row[0])] = row[1]
        else:
            users[int(row[0])] = bot.get_chat(row[0]).username

    logger.info('Database succesefull load')

    updater = Updater(bot=bot, use_context=True)
    job = updater.job_queue
    job.run_repeating(callback=newSavedUpdater,interval=60)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('secrettoall', send_toall))
    dispatcher.add_handler(MessageHandler(Filters.text(buttons), HandlerButtons))
    dispatcher.add_handler(CallbackQueryHandler(like))
    updater.start_polling(timeout=123)

