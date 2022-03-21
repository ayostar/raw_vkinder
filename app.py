import vk_api
import re
from random import randrange
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_auth import group_token
from db_functions import DB
from vk_functions import VK
from messages import *


vk = VK()
db = DB()


class Bot:
    def __init__(self, group_token):
        self.token = group_token
        self.vk_session = vk_api.VkApi(token=group_token)
        self.longpoll = VkLongPoll(self.vk_session)

    def write_msg(self, user_id, message, attachment = None):
        params = {
            'user_id': user_id,
            'message': message,
            'random_id': randrange(10 ** 7)}
        if attachment:
            params['attachment'] = attachment
        self.vk_session.method('messages.send', params)

    def loop_bot(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    listen_message_text = event.text.lower()
                    listen_user_id = event.user_id
                    return listen_message_text, listen_user_id

    def bot_start(self, listen_user_id):
        h_user_first_name, h_user_last_name, h_user_sex = vk.get_horney_user_info(listen_user_id)
        try:
            db_h_user_id = db.check_db_h_user(listen_user_id)

            if db_h_user_id is not None:
                self.bot_greeting(listen_user_id, h_user_first_name, h_user_last_name, h_user_sex)
            else:
                db.reg_new_user(listen_user_id, h_user_first_name, h_user_last_name)
                self.bot_greeting(listen_user_id, h_user_first_name, h_user_last_name, h_user_sex)
        except:
            print('Что-то не так с базой данных')

    def bot_greeting(self, listen_user_id, h_user_first_name, h_user_last_name, h_user_sex):
        h_user_city_id, h_user_city_title = vk.get_user_city(listen_user_id)
        h_user_age = vk.get_user_age(listen_user_id)

        self.write_msg(listen_user_id, f'Привет {h_user_first_name} {h_user_last_name}! Я бот - Vkinder\n'
                                       f'Я помогу тебе подобрать пару!\n'
                                       f'Согласно моим данным ты {h_user_sex}.\n')
        if h_user_city_title is not None:
            self.write_msg(listen_user_id, f'Ты из города {h_user_city_title}.\n')
        else:
            self.write_msg(listen_user_id, f'В твоем профиле не указан город.\n')

        if h_user_age is not None:
            self.write_msg(listen_user_id, f'Тебе {h_user_age}\n')
        else:
            self.write_msg(listen_user_id, f'В твоем профиле не указан твой возраст.\n')

    def bot_main_menu(self, listen_user_id):
        self.write_msg(listen_user_id, f'Для нового поиска введи "Vkinder"\n'
                                       f'Для просмотра избранного введи "Favorites"\n'
                                       f'Для просмотра черного списка введи "Blacklist"\n')

    def bot_query_sex(self, listen_user_id, listen_message_text):
        re_pattern_1 = re.search(r'((?:жен|дев|баб)+)', listen_message_text)
        re_pattern_2 = re.search(r'((?:муж|пар|пац|мальч)+)', listen_message_text)

        if re_pattern_2:
            d_user_sex = 2
        elif re_pattern_1:
            d_user_sex = 1
        elif listen_message_text == '0':
            d_user_sex = 0
        else:
            self.write_msg(listen_user_id, f'"{listen_message_text}" не соответствует мужчине или женщине.\n'
                                           f'Будем искать любой пол.')
            d_user_sex = 0

        return d_user_sex

    def bot_query_age(self, listen_user_id, listen_message_text):
        re_pattern = re.findall(r'(\d{2})', listen_message_text)
        if len(re_pattern) != 2:
            self.write_msg(listen_user_id, f'Данные "{listen_message_text}" не соответствуют критериям поиска.\n'
                                           f'Попробуйте ещё раз.\n')
            return None, None
        else:
            re_pattern.sort()

            d_user_age_from = int(re_pattern[0])
            d_user_age_to = int(re_pattern[1])
            return d_user_age_from, d_user_age_to

    def bot_query_country(self, listen_message_text):
        d_user_country_name = listen_message_text.title()
        d_user_country_id = vk.get_country_id(d_user_country_name)
        if d_user_country_id:
            return d_user_country_id
        else:
            return None

    def bot_query_city(self, listen_user_id, listen_message_text, d_user_country_id):
        d_user_city_title = listen_message_text.title()
        d_user_city_id = vk.get_cities_from_vk_db(d_user_city_title, d_user_country_id)

        if d_user_city_id is not None:
            return d_user_city_id
        else:
            self.write_msg(listen_user_id, f'Пользователей из города {d_user_city_title} увы нет.\n'
                                           f'Попробуй снова?')
            return None

    def bot_candidates(self, listen_user_id, d_user_lists):
        h_user_db_id = db.check_db_h_user(listen_user_id)
        d_users_count = len(d_user_lists)
        self.write_msg(listen_user_id, f'Количество найденных пользователей: {d_users_count}')
        if d_users_count != 0:
            for d_user in d_user_lists:
                self.write_msg(listen_user_id, f'Найден подходящий вариант:\n'
                                               f' Имя {d_user[1]}, Фамилия {d_user[2]}\n'
                                               f'Ссылка на страницу {d_user[4]}')

                photos_list = vk.get_photos_list(d_user[0])
                top_photos = vk.get_top_photos(3, photos_list)
                for photo in top_photos:
                    self.write_msg(listen_user_id, 'Фото:', attachment = {photo[-1]})

                self.write_msg(listen_user_id, '1 - Добавить, 2 - внести в черный список. "q" - выход из поиска\n')

                listen_message_text, listen_user_id = self.loop_bot()

                if listen_message_text == '1':
                    db.add_date_to_favorites(d_user[0], d_user[1], d_user[2], d_user[4], h_user_db_id)
                    db_d_user_id = db.check_db_d_user(d_user[0])
                    for photo in top_photos:
                        db.add_photos(photo[1], photo[0], db_d_user_id.id)
                    self.write_msg(listen_user_id, 'Вариант добавлен в список понравивщихся.')

                elif listen_message_text == '2':
                    db.add_to_black_list(d_user[0], d_user[1], d_user[2], d_user[4], h_user_db_id)
                    self.write_msg(listen_user_id, 'Вариант добавлен в черный список.')

                elif listen_message_text.lower() == 'q':
                    self.write_msg(listen_user_id, 'Больше не ищем')
                    self.bot_main_menu(listen_user_id)
                    break
                else:
                    continue

    def check_all_favorites(self, listen_user_id):
        found_favorite_list_users = db.check_db_favorites(listen_user_id)
        self.write_msg(listen_user_id, f'Избранные анкеты:')

        if len(found_favorite_list_users) == 0:
            self.write_msg(listen_user_id, f'В твоем списке нет анкет.\n')
        else:
            for nums, d_user in enumerate(found_favorite_list_users):
                self.write_msg(listen_user_id, f'{d_user.first_name}, {d_user.last_name}, {d_user.vk_link}')
                self.write_msg(listen_user_id, '1 - Удалить из избранного, 0 - Далее. \n"q" - Выход')
                listen_message_text, listen_user_id = self.loop_bot()

                if listen_message_text == '0':
                    if nums >= len(found_favorite_list_users) - 1:
                        self.write_msg(listen_user_id, f'Больше нет анкет.\n'
                                                       f'Vkinder - вернуться в меню\n')

                elif listen_message_text == '1':
                    db.delete_db_favorites(d_user.d_user_vk_id)
                    self.write_msg(listen_user_id, f'Анкета успешно удалена.')
                    if nums >= len(found_favorite_list_users) - 1:
                        self.write_msg(listen_user_id, f'Больше нет анкет.\n')

                elif listen_message_text.lower() == 'q':
                    self.bot_main_menu(listen_user_id)
                    break
                else:
                    continue

    def check_all_black_list(self, listen_user_id):
        found_black_list_users = db.check_db_black_list(listen_user_id)
        if len(found_black_list_users) == 0:
            self.write_msg(listen_user_id, f'В твоем списке нет анкет.\n')
        else:
            self.write_msg(listen_user_id, f'Анкеты в черном списке:')
            for nums, d_user in enumerate(found_black_list_users):
                self.write_msg(listen_user_id, f'{d_user.first_name}, {d_user.last_name}, {d_user.vk_link}')

                self.write_msg(listen_user_id, '1 - Удалить из черного списка, 0 - Далее. \n"q" - Выход')
                listen_message_text, listen_user_id = self.loop_bot()
                if listen_message_text == '0':
                    if nums >= len(found_black_list_users) - 1:
                        self.write_msg(listen_user_id, f'Больше нет анкет.\n'
                                                       f'Vkinder - вернуться в меню\n')

                elif listen_message_text == '1':
                    db.delete_db_blacklist(d_user.d_user_vk_id)
                    self.write_msg(listen_user_id, f'Анкета успешно удалена')
                    if nums >= len(found_black_list_users) - 1:
                        self.write_msg(listen_user_id, f'Это была последняя анкета.\n'
                                                       f'Vkinder - вернуться в меню\n')

                elif listen_message_text.lower() == 'q':
                    self.bot_main_menu(listen_user_id)
                    break
                else:
                    continue

    def bot(self):
        longpoll = VkLongPoll(self.vk_session)
        last_event = None
        d_user_sex = None
        d_user_age_from = None
        d_user_age_to = None
        d_user_country_id = None

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:

                if event.to_me:

                    listen_message_text = event.text.lower()
                    listen_user_id = event.user_id

                    if listen_message_text == 'Vkinder'.lower() and last_event is None:
                        self.bot_start(listen_user_id)
                        self.write_msg(listen_user_id, SEX)
                        last_event = 'wait for sex'

                    elif last_event == 'wait for sex':
                        d_user_sex = self.bot_query_sex(listen_user_id, listen_message_text)
                        self.write_msg(listen_user_id, AGE)
                        last_event = 'wait for age'

                    elif last_event == 'wait for age':
                        d_user_age_from, d_user_age_to = self.bot_query_age(listen_user_id, listen_message_text)
                        if d_user_age_from and d_user_age_to:
                            self.write_msg(listen_user_id, COUNTRY)
                            last_event = 'wait for country id'
                        else:
                            last_event = 'wait for age'

                    elif last_event == 'wait for country id':
                        d_user_country_id = self.bot_query_country(listen_message_text)
                        self.write_msg(listen_user_id, CITY)
                        last_event = 'wait for city id'

                    elif last_event == 'wait for city id':
                        d_user_city_id = self.bot_query_city(listen_user_id, listen_message_text, d_user_country_id)
                        if d_user_city_id is not None:
                            d_user_lists = vk.search_users(d_user_sex, d_user_age_from, d_user_age_to, d_user_city_id)
                            self.loop_bot()
                            self.bot_candidates(listen_user_id, d_user_lists)
                            self.bot_main_menu(listen_user_id)
                        else:
                            self.write_msg(listen_user_id, f'К сожалению пользователей из такого города нет')
                            self.bot_main_menu(listen_user_id)

                    elif listen_message_text == 'Favorites'.lower():
                        self.loop_bot()
                        self.check_all_favorites(listen_user_id)

                    elif listen_message_text == 'Blacklist'.lower():
                        self.loop_bot()
                        self.check_all_black_list(listen_user_id)

                    else:
                        self.bot_main_menu(listen_user_id)


if __name__ == '__main__':
    vkinder = Bot(group_token)
    vkinder.bot()


