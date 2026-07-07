import requests


class VKPublisherError(Exception):
    pass


class VKGroupAuthError(VKPublisherError):
    pass


class VKPublisher:
    def __init__(self, vk_api_key, group_id):
        self.vk_api_key = vk_api_key
        self.group_id = str(group_id).lstrip('-')

    def _check_response(self, response, action):
        if 'error' not in response:
            return response

        error = response['error']
        message = error.get('error_msg', 'Неизвестная ошибка VK API')

        if error.get('error_code') == 27 or 'групповой авторизации' in message.lower():
            raise VKGroupAuthError(
                f'{message}. Для публикации с фото нужен пользовательский токен VK '
                f'(права: wall, photos, groups), а не ключ сообщества.'
            )

        raise VKPublisherError(f'{action}: {message}')

    def upload_photo(self, image_url):
        upload_url_response = self._check_response(
            requests.get(
                'https://api.vk.com/method/photos.getWallUploadServer',
                params={
                    'access_token': self.vk_api_key,
                    'v': '5.236',
                    'group_id': self.group_id,
                },
            ).json(),
            'Не удалось получить адрес загрузки фото',
        )

        upload_url = upload_url_response['response']['upload_url']
        image_data = requests.get(image_url, timeout=60).content
        upload_response = requests.post(
            upload_url,
            files={'photo': ('image.jpg', image_data)},
            timeout=60,
        ).json()

        if 'photo' not in upload_response:
            raise VKPublisherError('VK не принял загруженное изображение')

        save_response = self._check_response(
            requests.get(
                'https://api.vk.com/method/photos.saveWallPhoto',
                params={
                    'access_token': self.vk_api_key,
                    'v': '5.236',
                    'group_id': self.group_id,
                    'photo': upload_response['photo'],
                    'server': upload_response['server'],
                    'hash': upload_response['hash'],
                },
            ).json(),
            'Не удалось сохранить фото на стене',
        )

        photo = save_response['response'][0]
        return f"photo{photo['owner_id']}_{photo['id']}"

    def publish_post(self, content, image_url=None):
        params = {
            'access_token': self.vk_api_key,
            'from_group': 1,
            'v': '5.236',
            'owner_id': f'-{self.group_id}',
            'message': content,
        }

        if image_url:
            params['attachments'] = self.upload_photo(image_url)

        response = self._check_response(
            requests.post('https://api.vk.com/method/wall.post', params=params, timeout=60).json(),
            'Не удалось опубликовать пост',
        )
        return response
