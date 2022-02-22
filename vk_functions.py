import vk_api

from vk_api.longpoll import VkLongPoll
from vk_auth import my_user_token, VK_version


vk_session = vk_api.VkApi(token=my_user_token)
longpoll = VkLongPoll(vk_session)


def get_horney_user_info(listen_user_id):
    params = {'user_id': listen_user_id, 'fields': 'sex, status, city, age'}
    h_user_info = vk_session.method('users.get', values=params)
    h_user_first_name = h_user_info[0].get('first_name')
    h_user_last_name = h_user_info[0].get('last_name')
    if h_user_info[0].get('sex') == 1:
        h_user_sex = 'Женщина'
    elif h_user_info[0].get('sex') == 2:
        h_user_sex = 'Мужчина'
    else:
        h_user_sex = 'Бесполый'

    return h_user_first_name, h_user_last_name, h_user_sex


def get_cities_from_vk_db(city_name):
    cities = vk_session.method('database.getCities',
                               {
                                   'access_token': my_user_token,
                                   'country_id': 1,
                                   'q': city_name,
                                   'need_all': True,
                                   'count': 100
                               })
    city_id = cities['items'][0]['id']
    return city_id


def search_users(sex, age_from, age_to, city):
    link_profile = 'https://vk.com/id'

    response = vk_session.method('users.search',
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
    date_users_list = []
    for element in response_list:
        if not element['is_closed'] and 'city' in element and element['blacklisted_by_me'] == 0:
            person = [
                element['id'],
                element['first_name'],
                element['last_name'],
                element['city']['title'],
                link_profile + str(element['id']),
            ]
            date_users_list.append(person)

    return date_users_list


def get_photos_list(dating_user):
    response = vk_session.method('photos.get',
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
        photos_list.append([likes_number, largest_photo_link])

    return photos_list


def get_top_photos(top_photos_number, photos_list):
    sorted_list = sorted(photos_list, reverse = True)
    sorted_list_items = len(sorted_list)
    if sorted_list_items >= top_photos_number:
        top_photos = sorted_list[:top_photos_number]
    else:
        top_photos = sorted_list[:sorted_list_items]

    return top_photos
