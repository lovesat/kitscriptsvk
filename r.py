import vk_api
import time
import re
import asyncio
import json
import requests
import random
import os
import telebot

TELEGRAM_TOKEN = '6009481163:AAEjGYTrImxil066b5oL_f_W35A-jfexiD4'
CHAT_ID = 5289076363

bot = telebot.TeleBot(TELEGRAM_TOKEN)

async def main():
    try:
        with open('tokens.txt', 'r') as f:
            tokens = f.readlines()
        if len(tokens) > 1:
            print("Выберите аккаунт для авторизации:")
            for i, token in enumerate(tokens):
                vk_session = vk_api.VkApi(token=token.strip())
                vk = vk_session.get_api()
                user = vk.users.get()[0]
                print(f"{i+1}. Аккаунт {user['first_name']} {user['last_name']}")
            choice = int(input("Введите номер аккаунта: "))
            token = tokens[choice-1].strip()
        else:
            token = tokens[0].strip()
            vk_session = vk_api.VkApi(token=token)
            vk = vk_session.get_api()
            user = vk.users.get()[0]
            print(f"Вы авторизовались в аккаунте {user['first_name']} {user['last_name']}")
    except FileNotFoundError:
        token = input("Введите токен от аккаунта ВКонтакте: ")
        with open('tokens.txt', 'w') as f:
            f.write(token + '\n')
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()
        user = vk.users.get()[0]
        print(f"Вы авторизовались в аккаунте {user['first_name']} {user['last_name']}")

    print("Выберите действие:")
    print("1. Перевести ID групп вк в числовое значение")
    print("2. Начать постинг")
    print("3. Сделать рассылку по беседам")
    print("4. Получить возможных друзей")
    print("5. Рассылка по возможным друзьям")
    print("6. ID пользователей создавших пост в группе")
    print("7. ID участников группы")
    choice = input("Введите цифру: ")

    if choice == '1':
        with open('grp_text.txt', 'r') as f:
            groups = f.read().splitlines()
        with open('groups.txt', 'w') as f:
            for group in groups:
                match = re.search(r'(?:https?://)?vk\.com/\S+', group)
                if match:
                    group_url = match.group()
                    group_id = group_url.split('/')[-1]
                    resolved_screen_name = vk.utils.resolveScreenName(screen_name=group_id)
                    if not resolved_screen_name:
                        continue
                    if isinstance(resolved_screen_name, list):
                        group_id = resolved_screen_name[0]['object_id']
                    else:
                        group_id = resolved_screen_name['object_id']
                    f.write(str(group_id) + '\n')

    elif choice == '2':
        while True:
            with open('tokens.txt', 'r') as f:
                tokens = f.read().splitlines()
            with open('groups.txt', 'r') as f:
                groups = f.read().splitlines()
            with open('message.txt', 'r', encoding='utf-8') as f:
                message = f.read()
            for token in tokens:
                vk_session = vk_api.VkApi(token=token)
                vk = vk_session.get_api()
                for group in groups:
                    post_id = None
                    try:
                        # Загрузка фотографии на сервер
                        photo_path = os.path.join('photos', 'ph.jpg')
                        upload_url = vk.photos.getWallUploadServer()['upload_url']
                        response = requests.post(upload_url, files={'photo': open(photo_path, 'rb')})
                        result = json.loads(response.text)
                        # Сохранение фотографии на сервере
                        photo = vk.photos.saveWallPhoto(server=result['server'], photo=result['photo'], hash=result['hash'])[0]
                        # Прикрепление фотографии к посту
                        attachments = ['photo{}_{}'.format(photo['owner_id'], photo['id'])]
                        vk.wall.post(owner_id=-int(group), post_id=post_id, message=message, attachments=attachments)
                        print(f"Пост успешно оставлен в группе {group}")
                        time.sleep(30)
                    except vk_api.exceptions.ApiError as e:
                        # Обработка ошибок
                        if e.code == 214 or e.code == 219:
                            try:
                                last_post = vk.wall.get(owner_id=-int(group), count=1)['items'][0]
                                post_id = last_post['id']
                                vk.wall.createComment(owner_id=-int(group), post_id=post_id, message=message)
                                print(f"Комментарий успешно оставлен в группе {group}")
                            except IndexError:
                                print(f"Нет записей в группе {group}")
                            except vk_api.exceptions.ApiError as e:
                                if e.code == 223 or e.code == 15:
                                    print(f"Комментарии закрыты в группе {group}")
                        time.sleep(30)
                    except vk_api.Captcha as captcha:
                            bot.send_photo(CHAT_ID, captcha.get_url())
                            print("Отправлена капча")
                            
                    @bot.message_handler(content_types=['text'])
                    def handle_text_message(message):
                        captcha_key = message.text
                        print(f"Получен ключ капчи: {captcha_key}")
                        captcha.try_again(captcha_key)
                        
            time.sleep(2)

    elif choice == '3':
            with open('tokens.txt', 'r') as f:
                tokens = f.read().splitlines()
            with open('message.txt', 'r', encoding='utf-8') as f:
                message = f.read()
            for token in tokens:
                vk_session = vk_api.VkApi(token=token)
                vk = vk_session.get_api()
                conversations = vk.messages.getConversations()['items']
                for conversation in conversations:
                    conversation_id = conversation['conversation']['peer']['id']
                    if conversation['conversation']['peer']['type'] == 'chat':
                        try:
                            random_id = random.randint(1, 2**32)  # Генерация случайного числа
                            vk.messages.send(peer_id=conversation_id, message=message, random_id=random_id)
                            print(f"Сообщение отправлено в беседу {conversation_id}")
                            time.sleep(30)
                        except vk_api.exceptions.ApiError as e:
                            print(f"Не удалось отправить сообщение в беседу {conversation_id}: {e}")
                            time.sleep(30)
                        except vk_api.Captcha as captcha:
                                bot.send_photo(CHAT_ID, captcha.get_url())
                                print("Отправлена капча")
                                
                        @bot.message_handler(content_types=['text'])
                        def handle_text_message(message):
                            captcha_key = message.text
                            print(f"Получен ключ капчи: {captcha_key}")
                            captcha.try_again(captcha_key)
            print("Рассылка завершена")

    elif choice == '4':
        # Получение возможных друзей
        url = 'https://api.vk.com/method/friends.getSuggestions?access_token=' + token + '&v=5.131'
        response = requests.get(url)
        data = json.loads(response.text)

        if 'response' in data:
            suggested_friends = data['response']['items']
            with open('fr_ids.txt', 'w') as f:
                for friend in suggested_friends:
                    f.write(str(friend['id']) + '\n')
        else:
            print('Ошибка при получении данных')

    elif choice == '5':
        # Рассылка по возможным друзьям
        with open('fr_ids.txt', 'r') as f:
            fr_ids = f.readlines()
        with open('message.txt', 'r', encoding='utf-8') as f:
            message = f.read()

        if len(fr_ids) == 0:
            print("Файл fr_ids.txt пуст")
        else:
            vk_session = vk_api.VkApi(token=token)
            vk = vk_session.get_api()

            for fr_id in fr_ids:
                fr_id = fr_id.strip()
                try:
                    vk.messages.send(user_id=fr_id, message=message, random_id=0)
                    print(f"Сообщение отправлено пользователю с ID {fr_id}")
                except vk_api.exceptions.ApiError as error:
                    if error.code == 901:
                        print(f"Личные сообщения отключены для пользователя с ID {fr_id}")
                    else:
                        print(f"Ошибка при отправке сообщения пользователю с ID {fr_id}")                    
                except vk_api.Captcha as captcha:
                    bot.send_photo(CHAT_ID, captcha.get_url())
                    print("Отправлена капча")
                            
                @bot.message_handler(content_types=['text'])
                def handle_text_message(message):
                    captcha_key = message.text
                    print(f"Получен ключ капчи: {captcha_key}")
                    captcha.try_again(captcha_key)

                time.sleep(30)

    elif choice == '6':
        group_id = input("Введите ID группы ВК: ")
        numeric_id = vk.groups.getById(group_id=group_id)[0]['id']
        print(f"Числовой ID группы: {numeric_id}")

        wall_posts = vk.wall.get(owner_id='-' + str(numeric_id), count=100)['items']
        poster_ids = set([post['from_id'] for post in wall_posts if post['from_id'] > 0])
        with open('grp_posters.txt', 'w') as f:
            for poster_id in poster_ids:
                f.write(str(poster_id) + '\n')
        print(f"ID пользователей, создавших посты в группе {group_id}, записаны в файл grp_posters.txt")

    elif choice == '7':
        group_id = input("Введите ID группы ВК: ")
        numeric_id = vk.groups.getById(group_id=group_id)[0]['id']
        print(f"Числовой ID группы: {numeric_id}")

        members = []
        offset = 0
        while True:
            response = vk.groups.getMembers(group_id=numeric_id, offset=offset, fields='is_closed', v=5.131)
            if 'items' in response:
                members += response['items']
                offset += 1000
            else:
                print('Ошибка при получении данных')
                break

            if offset >= response['count']:
                break

        with open('grp_members.txt', 'w') as f:
            for member in members:
                if member['is_closed']:
                    continue
                else:
                    f.write(str(member['id']) + '\n')
        print(f"ID участников группы {group_id} записаны в файл grp_members.txt")
        
    else:
        print("Некорректный выбор действия")

if __name__ == '__main__':
    asyncio.run(main())
    bot.polling()
