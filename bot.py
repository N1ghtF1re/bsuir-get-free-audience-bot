# -*- coding: utf-8 -*-
import vk_api
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

import sqlite3

from getEmployedFromDB import getEmployedAud
from getAudiences import getAudiencesList
from units import log # Ведение лога бота

log_filename = 'parser.log'
db_file =  '/projects/parser/db/schedule.sqlite' # Файл базы данных SQLite


STR_BUILDING = '{} корпус'
STR_FLOOR = '{} этаж'
STR_ANY = 'Любой'

token = 'token'
group_id = 0

class bot(object):
    def __init__(self, group_token, group_id):
        self.BUILDINGS_COUNT = 5

        self.floor = {
            1: range(0,5),
            2: range(3,7),
            3: range(1,6),
            4: range(0,6),
            5: range(2, 10)
        }

        self.chats = {}

        self.vk_session = vk_api.VkApi(token=group_token)
        self.group_id = group_id
        self.vk = self.vk_session.get_api()

        # Подключаемся к БД
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

        self.listenLongpoll()



    def addChatBuilding(self, chat_id, building = None):
        self.chats[chat_id] = building
    def getChatBuilding(self, chat_id):
        return self.chats.get(chat_id, None)

    def sendMessage(self, chat_id, message, keyboard = None):
        if keyboard:
            self.vk.messages.send(
                peer_id=chat_id,
                message=message,
                keyboard=keyboard.get_keyboard()
            )
        else:
            self.vk.messages.send(
                peer_id=chat_id,
                message=message
            )


    def getBuildingKeyboard(self):
        keyboard = VkKeyboard(one_time=True)

        for i in range(1, self.BUILDINGS_COUNT + 1):
            if i % 5 == 0:
                keyboard.add_line()

            keyboard.add_button(STR_BUILDING.format(i), color=VkKeyboardColor.PRIMARY)

        return keyboard


    def getFloorKeyboard(self, building):
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button(STR_FLOOR.format(STR_ANY), color=VkKeyboardColor.NEGATIVE)
        keyboard.add_line()
        for i, num in enumerate(self.floor[building]):
            if (i+1) % 5 == 0:
                keyboard.add_line()
                print(i)

            keyboard.add_button(STR_FLOOR.format(num), color=VkKeyboardColor.PRIMARY)


        return keyboard



    def sendDefault(self, chat_id):
        keyboard = self.getBuildingKeyboard()
        self.addChatBuilding(chat_id)
        self.sendMessage(chat_id, 'Выбери корпус', keyboard)

    def getNumber(self, text):
        try:
            return int(text)
        except ValueError:
            return None


    def searchFreeAuds(self, chat_id, floor):
        buildID = self.getChatBuilding(chat_id)
        allAuds = getAudiencesList(self.cursor,floor, buildID, db_file)
        employed = getEmployedAud(self.cursor); # Получаем множество занятых
        freeAud = allAuds - employed # Исключаем из множества всех аудиторий множество занятых аудиторий

        message = 'Свободные аудитории: \n'

        for aud in freeAud:
            message += aud + '\n'

        if not freeAud:
            message = 'Нет свободных аудиторий ;c\n'

        self.sendMessage(chat_id, message)

    def listenLongpoll(self):

        self.longpoll = VkBotLongPoll(self.vk_session, self.group_id)

        for event in self.longpoll.listen():

            if event.type == VkBotEventType.MESSAGE_EDIT:
                chat_id = event.raw['object']['from_id']
                self.sendDefault(chat_id)

            if event.type == VkBotEventType.MESSAGE_NEW:
                chat_id = event.raw['object']['peer_id']
                text = event.raw['object']['text']

                words = text.split()
                if len(words) == 2:
                    if words[1] == 'корпус':
                        building = self.getNumber(words[0])
                        if building and building in range(1, self.BUILDINGS_COUNT + 1):
                            self.addChatBuilding(chat_id, building)
                            keyboard = self.getFloorKeyboard(building)
                            self.sendMessage(chat_id, 'Выбери этаж', keyboard)
                        else:
                            self.sendDefault(chat_id)
                    elif words[1] == 'этаж' and self.getChatBuilding(chat_id):
                        floor = self.getNumber(words[0])
                        building = self.getChatBuilding(chat_id)
                        print(building)
                        print(floor)
                        print(self.floor[building])
                        if floor != None and floor in self.floor[building]:
                            print('2')
                            self.searchFreeAuds(chat_id, floor)
                            self.sendDefault(chat_id)
                        elif words[0] == STR_ANY:
                            print('3')
                            self.searchFreeAuds(chat_id, -1)
                            self.sendDefault(chat_id)
                        else:
                            print('4')
                            self.sendDefault(chat_id)
                    else:
                        self.sendDefault(chat_id)
                else:
                    self.sendDefault(chat_id)


            print(event.type)

    def __del__(self):
        self.conn.close()




logs = log.Log(log_filename) # Создаем объект логов

while True:
    try:
        if __name__ == '__main__':
            bot(token,group_id)
    except Exception as error_msg:
        print(error_msg)
        logs.write('ERROR!!!!!!' + str(error_msg))
