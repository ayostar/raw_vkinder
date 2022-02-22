import vk_api
import re
from random import randrange
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_auth import group_token
from db_functions import reg_new_user, add_date_to_favorites, add_photos, add_to_black_list, delete_db_blacklist,\
    delete_db_favorites, check_db_h_user, check_db_d_user, check_db_d_bl_user, check_db_black_list, check_db_favorites
from vk_functions import get_horney_user_info, search_users, get_cities_from_vk_db, get_photos_list, get_top_photos


vk_session = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk_session)


def loop_bot():
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                message_from_user = event.text.lower().strip()
                user_id = event.user_id
                return message_from_user, user_id


def write_msg(user_id, message, attachment=None, keyboard=None):
    params = {
        'user_id': user_id,
        'message': message,
        'random_id': randrange(10 ** 7),
        'attachment': attachment}
    if attachment:
        params['attachment'] = attachment
    if keyboard:
        params['keyboard'] = keyboard

    vk_session.method('messages.send', params)


def bot_greeting(listen_user_id, h_user_first_name, h_user_last_name, h_user_sex):
    write_msg(listen_user_id, f'Привет {h_user_first_name} {h_user_last_name}! Я бот - Vkinder\n'
                              f'Я помогу тебе подобрать пару!\n'
                              f'Согласно моим данным ты {h_user_sex}.\n')


def bot_main_menu(listen_user_id):
    write_msg(listen_user_id, f'Для нового поиска введи Vkinder"\n'
                              f'Для просмотра избранного введи "1"\n'
                              f'Для просмотра черного списка введи "2"\n')


def bot_query_sex(listen_user_id):
    write_msg(listen_user_id, f'Кого будем искать, мужчину или женщину?\n')
    listen_message_text, listen_user_id = loop_bot()

    # re_pattern_1 = re.search(r'((?:жен|дев|баб)+)', listen_message_text)
    re_pattern = re.search(r'((?:муж|пар|пац|мальч)+)', listen_message_text)
    if re_pattern:
        d_user_sex = 2
    else:
        d_user_sex = 1

    return d_user_sex


def bot_query_age(listen_user_id):
    write_msg(listen_user_id, f'Укажи возраст от и до лет?\n')
    listen_message_text, listen_user_id = loop_bot()

    re_pattern = re.findall(r'(\d{2})', listen_message_text)
    re_pattern.sort()

    d_user_age_from = re_pattern[0]
    d_user_age_to = re_pattern[1]

    return d_user_age_from, d_user_age_to


def bot_query_city(listen_user_id):
    write_msg(listen_user_id, f'Укажи город?\n')
    listen_message_text, listen_user_id = loop_bot()

    d_user_city_name = listen_message_text.capitalize()
    d_user_city_id = get_cities_from_vk_db(d_user_city_name)

    return d_user_city_id


def check_all_favorites(listen_user_id):
    found_favorite_list_users = check_db_favorites(listen_user_id)
    write_msg(listen_user_id, f'Избранные анкеты:')

    for nums, d_user in enumerate(found_favorite_list_users):
        write_msg(listen_user_id, f'{d_user.first_name}, {d_user.last_name}, {d_user.vk_link}')
        write_msg(listen_user_id, '1 - Удалить из избранного, 0 - Далее \nq - Выход')
        listen_message_text, listen_user_id = loop_bot()

        if listen_message_text == '0':
            if nums >= len(found_favorite_list_users) - 1:
                write_msg(listen_user_id, f'Больше нет анкет.\n'
                                          f'Vkinder - вернуться в меню\n')

        elif listen_message_text == '1':
            delete_db_favorites(d_user.d_user_vk_id)
            write_msg(listen_user_id, f'Анкета успешно удалена.')
            if nums >= len(found_favorite_list_users) - 1:
                write_msg(listen_user_id, f'Больше нет анкет.\n'
                                          f'Vkinder - вернуться в меню\n')

        elif listen_message_text.lower() == 'q':
            write_msg(listen_user_id, 'Vkinder - для активации бота.')
            break



def check_all_black_list(listen_user_id):
    found_black_list_users = check_db_black_list(listen_user_id)
    write_msg(listen_user_id, f'Анкеты в черном списке:')

    for nums, d_user in enumerate(found_black_list_users):
        write_msg(listen_user_id, f'{d_user.first_name}, {d_user.last_name}', {d_user.vk_link})

        write_msg(listen_user_id, '1 - Удалить из черного списка, 0 - Далее \nq - Выход')
        listen_message_text, listen_user_id = loop_bot()
        if listen_message_text == '0':
            if nums >= len(found_black_list_users) - 1:
                write_msg(listen_user_id, f'Больше нет анкет.\n'
                                    f'Vkinder - вернуться в меню\n')

        elif listen_message_text == '1':
            print(d_user.id)
            delete_db_blacklist(d_user.d_user_vk_id)
            write_msg(listen_user_id, f'Анкета успешно удалена')
            if nums >= len(found_black_list_users) - 1:
                write_msg(listen_user_id, f'Это была последняя анкета.\n'
                                    f'Vkinder - вернуться в меню\n')

        elif listen_message_text.lower() == 'q':
            write_msg(listen_user_id, 'Vkinder - для активации бота.')
            break


if __name__ == '__main__':
    while True:

        listen_message_text, listen_user_id = loop_bot()
        h_user_first_name, h_user_last_name, h_user_sex = get_horney_user_info(listen_user_id)

        re_pattern = re.findall(r'([А-Яа-яЁёA-Za-z0-9]+)', listen_message_text)

        if re_pattern:
            try:
                db_h_user_id = check_db_h_user(listen_user_id)
                bot_greeting(listen_user_id, h_user_first_name, h_user_last_name, h_user_sex)
                bot_main_menu(listen_user_id)
            except:
                if reg_new_user(listen_user_id, h_user_first_name, h_user_last_name):
                    db_h_user_id = check_db_h_user(listen_user_id)
                    bot_greeting(listen_user_id, h_user_first_name, h_user_last_name, h_user_sex)
                    write_msg(listen_user_id, f'Ты новенький. Я тебя зарегистрировал под номером {db_h_user_id}! Продолжай!')
                    bot_main_menu(listen_user_id)
                else:
                    write_msg(listen_user_id, 'Не удалось зарегистрировать пользователя')


            listen_message_text, listen_user_id = loop_bot()

            if listen_message_text == 'Vkinder'.lower():
                d_user_sex = bot_query_sex(listen_user_id)
                d_user_age_from, d_user_age_to = bot_query_age(listen_user_id)
                d_user_city_id = bot_query_city(listen_user_id)

                d_user_lists = search_users(d_user_sex, d_user_age_from, d_user_age_to, d_user_city_id)
                h_user_db_id = check_db_h_user(listen_user_id)

                for d_user in d_user_lists:
                    d_user_db_id = check_db_d_user(d_user[0])
                    d_user_bl_db_id = check_db_d_bl_user(d_user[0])

                    if d_user_db_id is not None or d_user_bl_db_id is not None:
                        continue

                    write_msg(listen_user_id, f'Найден подходящий вариант:\n'
                                              f' Имя {d_user[1]}, Фамилия {d_user[2]}\n'
                                              f'Ссылка на страницу {d_user[4]}')

                    photos_list = get_photos_list(d_user[0])
                    top_photos = get_top_photos(3, photos_list)
                    for photo in top_photos:
                        write_msg(listen_user_id, 'Фото:', attachment = {photo[-1]})

                    write_msg(listen_user_id, '1 - Добавить, 2 - внести в черный список. q - выход из поиска\n'
                                              'Нажми любой другой символ для продолжения.')
                    listen_message_text, listen_user_id = loop_bot()

                    if listen_message_text == '1':
                        add_date_to_favorites(d_user[0], d_user[1], d_user[2], d_user[4], h_user_db_id)
                        db_d_user_id = check_db_d_user(d_user[0])
                        for photo in top_photos:
                            add_photos(photo[1], photo[0], db_d_user_id.id)
                        write_msg(listen_user_id, 'Вариант добавлен в список понравивщихся.')

                    elif listen_message_text == '2':
                        add_to_black_list(d_user[0], d_user[1], d_user[2], h_user_db_id)
                        write_msg(listen_user_id, 'Вариант добавлен в черный список.')

                    elif listen_message_text.lower() == 'q':
                        write_msg(listen_user_id, 'Больше не ищем')
                        bot_main_menu(listen_user_id)
                        break

            elif listen_message_text == '1':
                check_all_favorites(listen_user_id)

            elif listen_message_text == '2':
                check_all_black_list(listen_user_id)
