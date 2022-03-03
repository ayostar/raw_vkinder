import vk_api

from vk_api.longpoll import VkLongPoll
from vk_auth import my_user_token, VK_version
import datetime
from db_functions import DB

db = DB()


class VK:

    def __init__(self):
        self.token = my_user_token
        self.vk_session = vk_api.VkApi(token=my_user_token)

    def get_user_age(self, listen_user_id):
        params = {'user_id': listen_user_id, 'fields': 'bdate'}
        h_user_info = self.vk_session.method('users.get', values = params)
        try:
            h_user_bdate = h_user_info[0].get('bdate')
            h_user_bdate_str = h_user_bdate.replace('.', '-')
            h_user_bdate_obj = datetime.datetime.strptime(h_user_bdate_str, '%d-%m-%Y')
            today = datetime.datetime.now().year
            h_user_age = today - h_user_bdate_obj.year
            return h_user_age
        except:
            return None

    def get_user_sex(self, sex_id):
        if sex_id == 1:
            h_user_sex = 'Женщина'
        elif sex_id == 2:
            h_user_sex = 'Мужчина'
        else:
            h_user_sex = 'Бесполый'
        return h_user_sex

    def get_user_city(self, listen_user_id):
        params = {'user_id': listen_user_id, 'fields': 'city'}
        h_user_info = self.vk_session.method('users.get', values = params)
        try:
            h_user_city_id = h_user_info[0]['city'].get('id')
            h_user_city_title = h_user_info[0]['city'].get('title')
            return h_user_city_id, h_user_city_title
        except:
            return None, None

    def get_user_country(self, listen_user_id):
        params = {'user_id': listen_user_id, 'fields': 'country'}
        h_user_info = self.vk_session.method('users.get', values = params)
        try:
            h_user_country_id = h_user_info[0]['country'].get('id')
            h_user_country_title = h_user_info[0]['country'].get('title')
            return h_user_country_id, h_user_country_title
        except:
            return None

    def get_horney_user_info(self, listen_user_id):
        params = {'user_id': listen_user_id, 'fields': 'sex'}
        h_user_info = self.vk_session.method('users.get', values = params)
        h_user_first_name = h_user_info[0].get('first_name')
        h_user_last_name = h_user_info[0].get('last_name')
        h_user_sex_id = h_user_info[0].get('sex')
        h_user_sex = self.get_user_sex(h_user_sex_id)

        return h_user_first_name, h_user_last_name, h_user_sex

    def get_cities_from_vk_db(self, city_name, country_id):
        cities = self.vk_session.method('database.getCities',
                                   {
                                       'access_token': my_user_token,
                                       'country_id': country_id,
                                       'q': city_name,
                                       'need_all': 1,
                                       'count': 100
                                   })
        print(cities)
        try:
            city_id = cities['items'][0]['id']
        except:
            city_id = None

        return city_id




    def get_countries_from_vk_db(self):
        countries_data = self.vk_session.method('database.getCountries',
                                           {
                                               'access_token': my_user_token,
                                               'need_all': 1,
                                               'count': 234
                                           })
        return countries_data


    def get_country_id(self, country_name):
        country_data = self.get_countries_from_vk_db()
        country_list = country_data['items']
        for countries in country_list:
            if countries['title'] == country_name:
                country_id = countries['id']
                return country_id


    def search_users(self, sex, age_from, age_to, city):
        link_profile = 'https://vk.com/id'

        response = self.vk_session.method('users.search',
                                     {'sort': 0,
                                      'count': 10,
                                      'city': city,
                                      'sex': sex,
                                      'status': 6,
                                      'age_from': age_from,
                                      'age_to': age_to,
                                      'has_photo': 1,
                                      'online': 1,
                                      'fields': 'blacklisted_by_me,'
                                                'can_send_friend_request,'
                                                'can_write_private_message,'
                                                'city,'
                                                'sex,'
                                                'relation'
                                      })
        response_list = response['items']
        raw_users_list = []
        for element in response_list:
            if not element['is_closed'] and 'city' in element and element['blacklisted_by_me'] == 0:
                person = [
                    element['id'],
                    element['first_name'],
                    element['last_name'],
                    element['city']['title'],
                    link_profile + str(element['id']),
                ]
                raw_users_list.append(person)
        date_users_list = []
        for d_user in raw_users_list:
            print(d_user[0])
            d_user_db_id = db.check_db_d_user(d_user[0])
            print(d_user_db_id)
            d_user_bl_db_id = db.check_db_d_bl_user(d_user[0])
            print(d_user_bl_db_id)
            if d_user_db_id is None and d_user_bl_db_id is None:
                date_users_list.append(d_user)

        return date_users_list



    def get_photos_list(self, dating_user):
        response = self.vk_session.method('photos.get',
                                     {
                                         'access_token': my_user_token,
                                         'v': VK_version,
                                         'owner_id': dating_user,
                                         'album_id': 'profile',
                                         'count': 50,
                                         'extended': 1,
                                         'photo_sizes': 1,
                                     })
        photos_count = len(response['items'])
        response_list = response['items']
        photos_list = []
        for photo in range(photos_count):
            likes_number = response_list[photo]['likes']['count']
            largest_photo_link = response_list[photo]['sizes'][-1].get('url')
            owner_id = response_list[photo].get('owner_id')
            media_id = response_list[photo].get('id')
            photo_id_string = f'photo{owner_id}_{media_id}'
            photos_list.append([likes_number, largest_photo_link, photo_id_string])
        return photos_list

    def get_top_photos(self, top_photos_number, photos_list):
        sorted_list = sorted(photos_list, reverse = True)
        sorted_list_items = len(sorted_list)
        if sorted_list_items >= top_photos_number:
            top_photos = sorted_list[:top_photos_number]
        else:
            top_photos = sorted_list[:sorted_list_items]
        print(top_photos)
        return top_photos

vk = VK()
# print(vk.get_cities_from_vk_db("Псков", 1))
# print(vk.get_cities_from_vk_db('Варшава', 160))
# print(vk.get_country_id('Poland'))
# print(vk.search_users(1, 38, 45, 1))
# top = vk.get_photos_list(1951791)
# print(vk.get_top_photos(3, top))

#
# vk_session = vk_api.VkApi(token=my_user_token)
# longpoll = VkLongPoll(vk_session)
#
#
# def get_user_age(listen_user_id):
#     params = {'user_id': listen_user_id, 'fields': 'bdate'}
#     h_user_info = vk_session.method('users.get', values=params)
#     try:
#         h_user_bdate = h_user_info[0].get('bdate')
#         h_user_bdate_str = h_user_bdate.replace('.', '-')
#         h_user_bdate_obj = datetime.datetime.strptime(h_user_bdate_str, '%d-%m-%Y')
#         today = datetime.datetime.now().year
#         h_user_age = today - h_user_bdate_obj.year
#         return h_user_age
#     except:
#         return None
#
#
# def get_user_sex(sex_id):
#     if sex_id == 1:
#         h_user_sex = 'Женщина'
#     elif sex_id == 2:
#         h_user_sex = 'Мужчина'
#     else:
#         h_user_sex = 'Бесполый'
#     return h_user_sex
#
#
# def get_user_city(listen_user_id):
#     params = {'user_id': listen_user_id, 'fields': 'city'}
#     h_user_info = vk_session.method('users.get', values=params)
#     try:
#         h_user_city_id = h_user_info[0]['city'].get('id')
#         h_user_city_title = h_user_info[0]['city'].get('title')
#         return h_user_city_id, h_user_city_title
#     except:
#         return None, None
#
#
# def get_user_country(listen_user_id):
#     params = {'user_id': listen_user_id, 'fields': 'country'}
#     h_user_info = vk_session.method('users.get', values=params)
#     try:
#         h_user_country_id = h_user_info[0]['country'].get('id')
#         h_user_country_title = h_user_info[0]['country'].get('title')
#         return h_user_country_id, h_user_country_title
#     except:
#         return None
#
#
# def get_horney_user_info(listen_user_id):
#     params = {'user_id': listen_user_id, 'fields': 'sex'}
#     h_user_info = vk_session.method('users.get', values=params)
#     print(h_user_info)
#     h_user_first_name = h_user_info[0].get('first_name')
#     h_user_last_name = h_user_info[0].get('last_name')
#     h_user_sex_id = h_user_info[0].get('sex')
#     h_user_sex = get_user_sex(h_user_sex_id)
#
#     return h_user_first_name, h_user_last_name, h_user_sex
#
# # print(get_horney_user_info(617501125))
# # print(get_user_age(617501125))
# # print(get_user_city(617501125))
# print(get_user_country(617501125))
#
#
# # def get_cities_from_vk_db(city_name):
# #     cities = vk_session.method('database.getCities',
# #                                {
# #                                    'access_token': my_user_token,
# #                                    'country_id': 1,
# #                                    'q': city_name,
# #                                    'need_all': True,
# #                                    'count': 100
# #                                })
# #     city_id = cities['items'][0]['id']
# #     return city_id
#
# def get_cities_from_vk_db(city_name, country_id):
#     cities = vk_session.method('database.getCities',
#                                {
#                                    'access_token': my_user_token,
#                                    'country_id': country_id,
#                                    'q': city_name,
#                                    'need_all': 1,
#                                    'count': 100
#                                })
#     city_id = cities['items'][0]['id']
#     return city_id
#
# print(get_cities_from_vk_db('Псков', 1))
#
#
# def get_countries_from_vk_db():
#     countries_data = vk_session.method('database.getCountries',
#                                {
#                                    'access_token': my_user_token,
#                                    'need_all': 1,
#                                    'count': 234
#                                })
#     return countries_data
#
# print(get_countries_from_vk_db())
#
# def get_country_id(country_name):
#     country_data = get_countries_from_vk_db()
#     country_list = country_data['items']
#     print(country_list)
#     for countries in country_list:
#         if countries['title'] == country_name:
#             country_id = countries['id']
#             return country_id
#
# print(get_country_id('Russia'))
#
#
# def search_users(sex, age_from, age_to, city):
#     link_profile = 'https://vk.com/id'
#
#     response = vk_session.method('users.search',
#                                  {'sort': 0,
#                                   'count': 10,
#                                   'city': city,
#                                   'sex': sex,
#                                   'status': 6,
#                                   'age_from': age_from,
#                                   'age_to': age_to,
#                                   'has_photo': 1,
#                                   'online': 1,
#                                   'fields': 'blacklisted_by_me,'
#                                             'can_send_friend_request,'
#                                             'can_write_private_message,'
#                                             'city,'
#                                             'sex,'
#                                             'relation'
#                                   })
#     response_list = response['items']
#     date_users_list = []
#     for element in response_list:
#         if not element['is_closed'] and 'city' in element and element['blacklisted_by_me'] == 0:
#             person = [
#                 element['id'],
#                 element['first_name'],
#                 element['last_name'],
#                 element['city']['title'],
#                 link_profile + str(element['id']),
#             ]
#             date_users_list.append(person)
#
#     return date_users_list
#
#
# def get_photos_list(dating_user):
#     response = vk_session.method('photos.get',
#                                  {
#                                      'access_token': my_user_token,
#                                      'v': VK_version,
#                                      'owner_id': dating_user,
#                                      'album_id': 'profile',
#                                      'count': 50,
#                                      'extended': 1,
#                                      'photo_sizes': 1,
#                                  })
#     photos_count = len(response['items'])
#     response_list = response['items']
#     photos_list = []
#     for photo in range(photos_count):
#         likes_number = response_list[photo]['likes']['count']
#         largest_photo_link = response_list[photo]['sizes'][-1].get('url')
#         photos_list.append([likes_number, largest_photo_link])
#
#     return photos_list
#
#
# def get_top_photos(top_photos_number, photos_list):
#     sorted_list = sorted(photos_list, reverse = True)
#     sorted_list_items = len(sorted_list)
#     if sorted_list_items >= top_photos_number:
#         top_photos = sorted_list[:top_photos_number]
#     else:
#         top_photos = sorted_list[:sorted_list_items]
#
#     return top_photos
