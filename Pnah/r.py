import vk_api
from threading import Thread
import os
import time
import random

def main():
    # Выбор способа авторизации
    auth_method = 2

    # Задержка между комментариями
    delay = int(input('Введите задержку между комментариями в секундах (0 - без задержки): '))

    # Выбор способа получения списка групп
    group_method = input('Выберите способ получения списка групп: 1. Группы на которые подписан 2. Использовать groups.txt: ')

    # Кодировка файла comments.txt
    encoding = input('Введите кодировку файла comments.txt: ')

    threads = []

    success_count = 0

    # Авторизация по токену
    if auth_method == 2:
        tokens_path = input('Укажите путь до txt файла tokens с токенами: ')
        with open(tokens_path, 'r') as f:
            tokens = f.read().splitlines()
        for token in tokens:
            vk_session = vk_api.VkApi(token=token)
            try:
                vk_session._auth_token()
                success_count += 1
            except vk_api.AuthError as error_msg:
                print(f'Ошибка авторизации по токену: {error_msg}')
                continue
            vk = vk_session.get_api()
            t = Thread(target=worker, args=(vk, delay, group_method, encoding))
            t.start()
            threads.append(t)
        print(f'Количество авторизованных аккаунтов: {success_count}')

    for t in threads:
        t.join()

def worker(vk, delay, group_method, encoding):
    if group_method == '1':
        # Получение списка групп на которые подписан пользователь
        groups = vk.groups.get()['items']
        # Запись списка групп в файл
        with open('groups.txt', 'w') as f:
            for group in groups:
                f.write(str(group) + '\n')
        # Чтение списка групп из файла
        with open('groups.txt', 'r') as f:
            groups = f.read().splitlines()
    elif group_method == '2':
        # Чтение списка групп из файла
        with open('groups.txt', 'r') as f:
            groups = f.read().splitlines()
    else:
        print('Неверный выбор способа получения списка групп')
        return

    # Чтение списка комментариев из файла
    comments = ['Комментарий']
    if os.path.exists('comments.txt'):
        with open('comments.txt', 'r', encoding=encoding) as f:
            comments = f.read().splitlines()
    else:
        print('Комментарии не были указаны')

    # Словарь для хранения ID последнего поста для каждой группы
    last_timestamp = int(time.time())

    while True:
        try:
            # Ждём 30 секунд перед тем, как проверить новые посты
            time.sleep(delay)

            for group_id in groups:
                group_id = int(group_id)
                # Получаем последний пост в группе
                posts = vk.wall.get(owner_id=-group_id, count=10, offset=0, filter='all', latest=1)['items']

                for post in posts:
                    if post['date'] > last_timestamp:
                        # Выбор случайного комментария из списка
                        comment_text = random.choice(comments)
                        # Оставляем комментарий
                        vk.wall.createComment(owner_id=-group_id, post_id=post['id'], message=comment_text)

                        last_timestamp = post['date']

                        print(f'Оставлен комментарий в группе {group_id}')
        except Exception:
            continue

if __name__ == '__main__':
    main()