from flask import Flask, request
import vk_api, json
from vk_api.utils import get_random_id
from settings import token_id, confirmation_token, group_vk_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import pandas as pd
import csv
import time
import re
from multiprocessing import Process

app = Flask(__name__)


class Bot:

    def __init__(self, id, text, random, keyboard2, attachment):
        self.id = id
        self.text = text
        self.random_id = random
        self.keyboard3 = keyboard2
        self.attachment = attachment

    # Функция для запука запроса
    def session(token):
        vk_session = vk_api.VkApi(token = token)
        return vk_session

    # Функция для передачи сообещний клиентам
    def send(self):
        attachment = ''
        if self.attachment != '':
            if self.attachment[0] == '/':
                upload = vk_api.VkUpload(vk_session)
                photo = upload.photo_messages(self.attachment)
                owner_id = photo[0]['owner_id']
                photo_id = photo[0]['id']
                access_key = photo[0]['access_key']
                attachment = f'photo{owner_id}_{photo_id}_{access_key}'

            else:
                attachment = self.attachment
        vk.messages.send(peer_id=self.id, random_id=self.random_id, message=self.text, keyboard=self.keyboard3, attachment=attachment)

    # Метод для рассылки спама
    def spam_send(ids, random_id, attachment):
        vk.messages.send(peer_ids=ids, random_id=random_id, attachment=attachment)

    # Метод для ответа администратору
    def admin_send(peer_id, random_id, message):
        vk.messages.send(peer_id=peer_id, random_id=random_id, message=message)

    # Метод для уведомления о новой заявке
    def notice(id_client, flag):
        # Создаем список администраторов 1 уровня
        notice_list = '/home/Zacher/mysite/commands_data.json'
        with open(notice_list, encoding='utf-8') as file:
            notice_json = json.load(file)
        notice_admins = notice_json["administrators"]
        ids_admins = list()
        for i in notice_admins.items():
            id_admin, level_admin = i
            if level_admin == '1':
                ids_admins.append(id_admin)

        # Считываем информацию о клиенете из базы
        forms = '/home/Zacher/mysite/forms.csv'
        with open(forms, "r", newline="") as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == str(id_client):
                    break

        message_id=get_random_id()
        # Создаем клеше, с инфомацией и ссылкой на пользователя
        text = f'{row}\nhttps://vk.com/id{row[0]}'
        # Если payload кнопки был сделан при выборе времени
        if flag == "{\"button\":\"time\"}":
            vk.messages.send(peer_ids=ids_admins, random_id = message_id, message=f'Пользователь записался на занятие\n'+text)
        # Если текст кнопки был 'Позвать человека'
        elif flag == 'Позвать человека':
            vk.messages.send(peer_ids=ids_admins, random_id = message_id, message=f'Пользователь просит помощи у человека\n'+text)

    # Функция для передачи стикеров
    def sticker(peer_id, random_id, sticker_id):
        vk.messages.send(peer_id=peer_id, random_id=random_id, sticker_id = sticker_id)


    # Считывание фраз для бота
    j = open('/home/Zacher/mysite/string.json', encoding='utf-8')
    cliche_text = json.load(j)


class Keyboard:

    def __init__(self, text, payload2, one_time, inline):
        self.text = text
        self.payload = payload2
        self.inline = inline
        self.one_time = one_time

    # Пустая клавиатура
    def empty():
        keyboard = VkKeyboard(one_time=True)
        return keyboard.get_empty_keyboard()

    # Основная клавиатура
    def keyboard(self):

        # Функция для выбора цвета клавиатуры
        def color(num):
            num = int(num)
            if num == 0:
                return VkKeyboardColor.NEGATIVE
            elif num == 1:
                return VkKeyboardColor.POSITIVE
            elif num == 2:
                return VkKeyboardColor.PRIMARY
            else:
                return VkKeyboardColor.SECONDARY

        # Считываем фразы для клавиш
        g = open('/home/Zacher/mysite/keyboard_text.json', encoding='utf-8')
        cliche_keyboard = json.load(g)
        # Объект клавиатуры
        keyboard = VkKeyboard(one_time=self.one_time, inline = self.inline)
        # Количество клавиш для вывода
        count_element = len(cliche_keyboard[self.text])
        sum = 0
        flag = 0
        # Цикл перебора клавишей
        if len(cliche_keyboard[self.text]) > 4:
            max_in_line = 2
        else:
            max_in_line = 1
        for i in cliche_keyboard[self.text]:
            keyboard.add_button(i[0], color=color(i[1]), payload = self.payload)
            flag += 1
            # Флаг, чтобы понять, что уже 2 клавиши на экране
            if flag == max_in_line:
                flag = 0
                keyboard.add_line()
            sum += 1
            # Условия, чтобы после последней клавиши не ставить новую линию
            if sum+1 == count_element:
                break
        # Объект последней клавиши
        last_button = cliche_keyboard[self.text][count_element-1]
        keyboard.add_button(last_button[0], color=color(last_button[1]), payload = self.payload)
        return keyboard.get_keyboard()


# Класс для обработки данных
class Data:

    # Метод для добавления айди, ФИ
    def add_id_user(id_client, vk, status):
        #использвуем метод из vk api, которого нет в бибиотеке vk_api
        user = vk.method("users.get", {"user_ids": id_client})
        columns = ['id_user', 'first_name', 'last_name', 'group', 'time', 'phone','status','datetime']
        df = pd.DataFrame([[str(id_client), user[0]['first_name'], user[0]['last_name'], '', '', '', status, '']], columns=columns)
        df.to_csv('/home/Zacher/mysite/forms.csv', mode = 'a', header=False, index = False)
        # Закрываем файл
        df = 0

    # Метод для добавления группы
    def add_group(id_client, group):
        df = pd.read_csv('/home/Zacher/mysite/forms.csv')
        df.loc[df.id_user == id_client, 'group'] = group
        df.to_csv('/home/Zacher/mysite/forms.csv', index = False)
        df = 0

    # Метод для добавления расписания группы
    def add_time(id_client, time):
        df = pd.read_csv('/home/Zacher/mysite/forms.csv')
        df.loc[df.id_user == id_client, 'time'] = time
        df.to_csv('/home/Zacher/mysite/forms.csv', index = False)
        df = 0

    # Метод для добавления отметки времени
    def add_datetime(id_client):
        df = pd.read_csv('/home/Zacher/mysite/forms.csv')
        df.loc[df.id_user == id_client, 'datetime'] = time.time()
        df.to_csv('/home/Zacher/mysite/forms.csv', index = False, float_format='%.0f')
        df = 0

    # Метод для добавления номера телефона времени
    def add_phone(id_client, phone):
        df = pd.read_csv('/home/Zacher/mysite/forms.csv')
        df.loc[df.id_user == id_client, 'phone'] = phone
        df.to_csv('/home/Zacher/mysite/forms.csv', index = False)
        df = 0

    # Метод для добавления номера телефона времени
    def add_status(id_client, status):
        df = pd.read_csv('/home/Zacher/mysite/forms.csv')
        df.loc[df.id_user == id_client, 'status'] = status
        df.to_csv('/home/Zacher/mysite/forms.csv', index = False, float_format='%.0f')
        df = 0

    # Метод для проверки наличия пользователя в базе
    def check(id_client):
        #return not bool(len(Data.forms.loc[Data.forms.id_user ==  int(id_client)]))
        forms = '/home/Zacher/mysite/forms.csv'
        with open(forms, "r", newline="") as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == str(id_client):
                    return False
        return True

    # Метод для проверки статуса клиента либо Ученик, либо Новый
    # Если ученик, то бот ему не пишет, если Новый, то отвечает на все бот
    def check_status(id_client):
        forms = '/home/Zacher/mysite/forms.csv'
        with open(forms, "r", newline="") as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == str(id_client) and row[6] == 'Ученик':
                    return False
        return True

    # Метод для ведения лога
    def logs(id_client, message, time):
        with open('/home/Zacher/mysite/logs.csv', 'a') as file:
            file.write(f'{id_client},{message},{int(time)}\n')


# vk.messages.getConversations()['items'][0]['conversation']['peer']['id']
class Commands:

    # Метод для блокировки(разблокировки) исполнения новых команд
    def lock_command(locker, message_id):
        lock_list = '/home/Zacher/mysite/lock.json'
        with open(lock_list, encoding='utf-8') as file:
            lock_json = json.load(file)

        def lock():
            lock_json["lock_commands"] = False
            lock_json["id_asp"] = message_id
            with open(lock_list, 'w') as outfile:
                json.dump(lock_json, outfile)

        def unlock():
            lock_json["lock_commands"] = True
            with open(lock_list, 'w') as outfile:
                json.dump(lock_json, outfile)

        if locker == 'lock':
            return lock()
        elif locker == 'unlock':
            return unlock()
        elif locker == 'check':
            return lock_json["lock_commands"]

    # Методя для проверки пользователя на администрирование
    def check_access(id_user):
        id_user = str(id_user)
        admin_list = '/home/Zacher/mysite/commands_data.json'
        with open(admin_list, encoding='utf-8') as file:
            admins = json.load(file)
        admin = admins['administrators'].get(id_user, False)
        if admin != False:
            return int(admin)
        else:
            return False

    #Метод для добавления новых администраторов
    def add_admin(id_user, level):
        id_user = str(id_user)
        admin_list = '/home/Zacher/mysite/commands_data.json'
        with open(admin_list, encoding='utf-8') as file:
            admins = json.load(file)
        if admins['administrators'].get(id_user, False) == False:
            admins['administrators'][id_user] = str(level)
            with open(admin_list, 'w') as outfile:
                json.dump(admins, outfile)
            return f'Администратор {id_user} с уровнем {level} добавлен'
        else:
            return f'Администратор {id_user} с уровнем {admins["administrators"][id_user]} уже существует'

    def remove_admin(id_admin):
        check_list = '/home/Zacher/mysite/commands_data.json'
        with open(check_list, encoding = 'utf-8') as file:
            check_json = json.load(file)

        admin_delete = check_json["administrators"].pop(id_admin, False)
        with open(check_list, 'w') as outfile:
            json.dump(check_json, outfile)
        if not admin_delete:
            return f'Администратор {id_admin} не найден'
        return f'Администратор {id_admin} удален'

    def check_admin():
        check_list = '/home/Zacher/mysite/commands_data.json'
        with open(check_list, encoding = 'utf-8') as file:
            check_json = json.load(file)
        admin_list = list(check_json["administrators"].keys())
        for i in range(len(admin_list)):
            admin_list[i] = f'https://vk.com/id{admin_list[i]}\n'
        return admin_list

    # Метод для для рассылки сообщения
    def spam(id_admin, spam, message_id):
        if Commands.lock_command('check', message_id):
            Commands.lock_command('lock', message_id)
            count = 0
            admin_list = '/home/Zacher/mysite/commands_data.json'
            with open(admin_list, encoding='utf-8') as file:
                spam_list = json.load(file)
            spam_list = spam_list['spam_list']
            for i in spam_list:
                try:
                    i.remove(id_admin)
                    break
                except:
                    continue
            for i in range(len(spam_list)):
                count += len(spam_list[i])
                message_id=get_random_id()
                Bot.spam_send(spam_list[i], message_id, spam)
            message_id=get_random_id()
            Commands.lock_command('unlock', message_id)
            Bot.admin_send(id_admin, message_id, f'Было отправлено {count} сообщений')
        else:
            Bot.admin_send(id_admin, message_id, f'Сейчас выполняеся другая команда, попробуйте позже')

    # Метод для обновления списков для рассылки
    def access_spam(id_admin, random_id, message_id):
        if Commands.lock_command('check', message_id):
            Commands.lock_command('lock', message_id)
            # Время начала обнавления
            start = time.time()
            spam_list = set()
            # Перебор участников группы group_vk_id группы в настройках
            for i in vk.groups.getMembers(group_id = group_vk_id)['items']:
                if vk.messages.isMessagesFromGroupAllowed(group_id = group_vk_id, user_id = i)['is_allowed']:
                    spam_list.add(i)

            # Получение списка диалогов
            # Количество последних переписок
            conversations = vk.messages.getConversations(count = 110)
            # Количество полученых переписок
            count = len(conversations['items'])
            items = conversations['items']

            # Перебор диалогов
            for i in range(count):
                id_spam = items[i]['conversation']['peer']['id']
                # Если id отрицательный, то это группа. Группам не пишем
                id_spam = id_spam if id_spam > 0 else 1
                if vk.messages.isMessagesFromGroupAllowed(group_id = group_vk_id, user_id = id_spam)['is_allowed']:
                    spam_list.add(id_spam)
            # Превращаем множество в список
            lst = list(spam_list)
            count_spam_list = len(lst)
            # Разбиваем список на списки по 100 айди, так как за раз можно отправить сообщение только 100 людям
            spam_list = [lst[i:i + 100] for i in range(0, len(lst), 100)]
            admin_list = '/home/Zacher/mysite/commands_data.json'
            with open(admin_list, encoding='utf-8') as file:
                spam_json = json.load(file)
            spam_json["spam_list"] = spam_list
            with open(admin_list, 'w') as outfile:
                json.dump(spam_json, outfile)
            # Финиш обновления
            finish = time.time()
            Commands.lock_command('unlock', message_id)
            Bot.admin_send(id_admin, random_id, f'Список для рассылки обновлен за {int(finish-start)} секунд. В списке {count_spam_list}')
        else:
            Bot.admin_send(id_admin, random_id, f'Сейчас выполняется другая команда, попробуйте позже')

    # Метод для добавление нового расписания
    def new_timesheet(timesheet):
        timesheet_list = '/home/Zacher/mysite/commands_data.json'
        with open(timesheet_list, encoding='utf-8') as file:
            timesheet_json = json.load(file)
        timesheet_json["timesheet"] = timesheet
        with open(timesheet_list, 'w') as outfile:
            json.dump(timesheet_json, outfile)
        return f'Добавлено новое расписание {timesheet}'

    # Метод для проверки правильности команды
    def check_commands(command):
        check_list = '/home/Zacher/mysite/string.json'
        with open(check_list, encoding = 'utf-8') as file:
            check_json = json.load(file)
        return command in check_json['/help']

# Функция для отправки сообщения с клавиатурой
def message_new(text_button, text_chat, id, random_id, payload1, attachment,one_time, inline):
    # Выбор клавиатуры класса Кейборд
    if payload1 != 'empty':
        payload1 = json.loads(payload1)
        keyboard = Keyboard(text_button, payload1, one_time, inline).keyboard()
    else:
        keyboard = Keyboard.empty()
    # Отправка данных для класса БОТ
    bot_sender = Bot(id, Bot.cliche_text[text_chat], random_id, keyboard, attachment)
    bot_sender.send()


# Функция для удаления эмодзи
def deEmojify(text):
    no_smile = ''
    for i in text:
        # Конвертация эмодзи в код
        smile = (f'{ord(i)}')
        if len(smile) != 6 and smile != '9989':
            no_smile += i
    return no_smile


# Ативация сессии
vk_session = Bot.session(token_id)
vk = vk_session.get_api()

img_no_button = '/home/Zacher/mysite/image/no_button.jpg'

not_img = ''

#with open('/home/Zacher/mysite/bin.txt', 'w') as file:
#file.write(text_user)
@app.route('/', methods=['POST'])
def events():
    # получаем данные из запроса
    data = request.get_json(force=True, silent=True)
    # ВКонтакте в своих запросах всегда отправляет поле type:
    # проверяем тип пришедшего события
    if data['type'] == 'confirmation':
        # если это запрос защитного кода
        # отправляем его
        return confirmation_token

    # если же это сообщение, отвечаем пользователю
    elif data['type'] == 'message_new':
        # Получаем ID сообщения
        id_message = data['object']['message']['id']
        # Получаем ID пользователя
        id_user = data['object']['message']['from_id']
        # Получаем текст сообщения без смайликов
        text_user = deEmojify(data['object']['message']['text'])
        # Получаем информацию об нажатии на кнопку Я ученик
        check_status = Data.check_status(id_user)
        # Получаем случайный id
        message_id=get_random_id()
        Data.logs(id_user, text_user, time.time())
        # Если сообщение это не команда и пишет пользователь не нажавший кнопку Я ученик, либо фразу Начать (чтобы любой мог вернуть бота)
        # начинаем обрабатывать событие
        if (check_status or text_user == 'Начать') and text_user[0] != '/':
            # Отправляем сообщение по нажатию кнопки Начать
            if text_user == 'Начать':
                message_new(text_user, text_user, id_user, message_id, "{\"button\":\"start\"}", not_img,False, True)
                # Если человека у человека был статус Ученик, но он решил вернуть бота, меняем ему статус
                if not check_status:
                    Data.add_status(int(id_user), 'Новый')

            # Если введен номер телефона, добавляем в базу
            elif re.search('^((8|\+7)[\- ]?)?(\(?\d{3}\)?[\- ]?)?[\d\- ]{7,10}$', text_user) != None:
                Bot.sticker(id_user, message_id, '9046')
                Data.add_phone(id_user, text_user)

            # Если это нераспознанный текст, у известных текстов есть payload
            elif data['object']['message'].get('payload') == None:
                if Data.check(id_user):
                    message_new('Начать', 'Начать', id_user, message_id, "{\"button\":\"start\"}", not_img,False, True)
                else:
                    message_new('Непонятно', 'Непонятно', id_user, message_id, "{\"button\":\"start\"}", not_img,False, True)

            # Отправляем сообщение по нажатию кнопки Назад
            elif text_user == 'Назад':
                # Если кнока была нажата в разделе групп
                if data['object']['message']['payload'] == "{\"button\":\"group\"}":
                    message_new('Начать', 'Начать', id_user, message_id, "{\"button\":\"start\"}", not_img,False, True)
                # Если кнопка была нажата в разделе расписания
                elif data['object']['message']['payload'] == "{\"button\":\"time\"}":
                    message_new('Записаться', 'Записаться_назад', id_user, message_id, "{\"button\":\"group\"}", not_img,True, False)
                # Если кнопка была нажата в разделе вопросов
                elif data['object']['message']['payload'] == "{\"button\":\"question\"}":
                    message_new('Начать', 'Начать', id_user, message_id, "{\"button\":\"start\"}", not_img,False, True)

            # Выбор кнопки позвать человека
            elif text_user == 'Позвать человека':
                # запускаем метод уведомления администраторов
                Bot.notice(id_user, 'Позвать человека')
                message_new('', "Позвать человека", id_user, message_id, "empty", not_img,True, False)
                # Если человека нет в базе, то добавить его со статусом Ученик
                if Data.check(id_user):
                    Data.add_id_user(int(id_user), vk_session, 'Ученик')
                    Data.add_datetime(id_user)
                # Если человек в базе есть, то изменить его статус на ученик
                else:
                    Data.add_status(int(id_user), 'Ученик')
                    Data.add_datetime(id_user)

            # Выбор сообщения после нажатия Начать
            elif data['object']['message']['payload'] == "{\"button\":\"start\"}":
                # Отправляем сообщение по нажатию кнопки Записаться
                if text_user == 'Записаться':
                    # Если человека нет в нашей Базе, то добавляем его, со статусом Новый
                    if Data.check(id_user):
                        message_new(text_user, text_user, id_user, message_id, "{\"button\":\"group\"}", img_no_button,True, False)
                        Data.add_id_user(int(id_user), vk_session, 'Новый')
                    else:
                        message_new(text_user, text_user+'_назад', id_user, message_id, "{\"button\":\"group\"}", not_img,True, False)

                # Отправляем сообщение по нажатию кнопки Задать вопрос
                elif text_user == 'Задать вопрос':

                    if Data.check(id_user):

                        message_new(text_user, text_user, id_user, message_id, "{\"button\":\"question\"}", img_no_button,True, False)
                        Data.add_id_user(int(id_user), vk_session ,'Новый')
                    else:
                        message_new(text_user, text_user+'_назад', id_user, message_id, "{\"button\":\"question\"}", not_img,True, False)

                elif text_user == 'Я ученик школы':
                    message_new('', text_user, id_user, message_id, "empty", not_img, False, False)
                    if Data.check(id_user):
                        Data.add_id_user(int(id_user), vk_session, 'Ученик')
                        Data.add_datetime(id_user)
                    else:
                        Data.add_status(int(id_user), 'Ученик')
                        Data.add_datetime(id_user)

            # Отправка ответа на вопросы
            elif data['object']['message']['payload'] == "{\"button\":\"question\"}":
                if text_user == 'Расписание':
                    timesheet_list = '/home/Zacher/mysite/commands_data.json'
                    with open(timesheet_list, encoding='utf-8') as file:
                        timesheet_json = json.load(file)
                    timesheet = timesheet_json["timesheet"]
                    message_new('Задать вопрос', text_user, id_user, message_id, "{\"button\":\"question\"}", timesheet,True, False)
                elif text_user in ['Возраста', 'Направления', 'На занятии', 'Адрес', 'Контакты']:
                    message_new('Задать вопрос', text_user, id_user, message_id, "{\"button\":\"question\"}", not_img,True, False)

            # Отправляем сообщение по нажатию кнопки Группы
            elif data['object']['message']['payload'] == "{\"button\":\"group\"}":
                message_new(text_user, "Выбрать время", id_user, message_id, "{\"button\":\"time\"}", not_img, True, False)
                Data.add_group(id_user, text_user)
                Data.add_datetime(id_user)

            # Отправляем сообщение по нажатию кнопки Расписания
            elif data['object']['message']['payload'] == "{\"button\":\"time\"}":
                message_new('', "Конец", id_user, message_id, "empty", not_img,True, False)
                Bot.notice(id_user, "{\"button\":\"time\"}")
                Data.add_time(id_user, text_user)
                Data.add_datetime(id_user)

        # Если сообщение это команда
        elif text_user[0] == '/':
            # Путь к файлу с блокираторами команд
            lock_list = '/home/Zacher/mysite/lock.json'
            with open(lock_list, encoding='utf-8') as file:
                lock_json = json.load(file)
            # Получаем id сообщения с последней запустившейся командой
            id_message_commands = lock_json['id_asp']
            # Получаем уровень доступа администратора
            level_admin = Commands.check_access(id_user)
            # Разбиваем команду на список
            parrametrs = text_user.split()
            # Проверка уровня доступа администратора
            # Если это команда из сообщения которое сейчас обрабатывается, то НЕ запускать команду заного
            check_commands = Commands.check_commands(parrametrs[0])
            if level_admin in [1, 2, 3] and id_message != id_message_commands:
                if check_commands:
                    if parrametrs[0] == '/help':
                        message_new('', "Liza_code", id_user, message_id, "empty", 'audio2000141460_456240403',True, False)
                        message_new('', '/help_about', id_user, message_id+1, "empty", not_img,True, False)
                    elif level_admin in [1, 2]:
                        # Выполнение команды на спам
                        if parrametrs[0] == '/sp':
                            t1 = Process(target=Commands.spam, args=(id_user, parrametrs[1], message_id,))
                            t1.start()
                            return 'ok'
                            # Commands.spam(id_user, parrametrs[1], message_id)
                        elif parrametrs[0] == '/nts':
                            text_commands = Commands.new_timesheet(parrametrs[1])
                            Bot.admin_send(id_user, message_id, text_commands)

                        elif level_admin in [1]:
                            # Выполнение команды на добавление нового администратора
                            if parrametrs[0] == '/aa':
                                text_commands = Commands.add_admin(parrametrs[1], parrametrs[2])
                                # Отправка сообщения об успешности добавления
                                Bot.admin_send(id_user, message_id, text_commands)
                            elif parrametrs[0] == '/ca':
                                text_commands = Commands.check_admin()
                                Bot.admin_send(id_user, message_id, text_commands)
                            elif parrametrs[0] == '/dela':
                                text_commands = Commands.remove_admin(parrametrs[1])
                                Bot.admin_send(id_user, message_id, text_commands)
                            # Выполнеие команды обновления списка доступных пользователей для рассылки
                            elif parrametrs[0] == '/asp':
                                t1 = Process(target=Commands.access_spam, args=(id_user,  message_id, id_message,))
                                t1.start()
                                return 'ok'
                                # Commands.access_spam(id_user,  message_id, id_message)

                else:
                    message_new('', "Команда", id_user, message_id, "empty", not_img,True, False)
            # Если запрошенной команды не существует

    elif data['type'] == 'message_deny':
        Data.logs(id_user, 'message_deny', time.time())
        id_user = data['object']['user_id']
        id_list = '/home/Zacher/mysite/commands_data.json'
        with open(id_list, encoding ='utf-8') as file:
            id_json = json.load(file)
        count = len(id_json['spam_list'])
        for i in range(count):
            try:
                id_json['spam_list'][i].remove(id_user)
                break
            except:
                continue
        with open(id_list, 'w') as outfile:
            json.dump(id_json, outfile)

    elif data['type'] == 'message_allow':
        Data.logs(id_user, 'message_allow', time.time())
        id_user = data['object']['user_id']
        id_list = '/home/Zacher/mysite/commands_data.json'
        with open(id_list, encoding ='utf-8') as file:
            id_json = json.load(file)
        count = len(id_json['spam_list'])
        for i in range(count):
            if len(id_json['spam_list'][i]) < 100:
                id_json['spam_list'][i].append(id_user)
                break
            elif i+1 == count:
                id_json['spam_list'].append(list((id_user,)))
            else:
                continue
        with open(id_list, 'w') as outfile:
            json.dump(id_json, outfile)
    # возвращаем серверу VK "ok" и код 200
    return 'ok'