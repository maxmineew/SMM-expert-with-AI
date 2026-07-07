# SMM-эксперт с ИИ

Flask-приложение для генерации постов и изображений через GigaChat и автопубликации во ВКонтакте.

**Долгий цикл постов и ручная публикация → генерация текстов и визуала под бренд + автопостинг VK → регулярный контент без рутины.**

## Возможности

- Генерация текста поста по теме и тону (GigaChat)
- Генерация изображения к посту (GigaChat)
- Автопубликация в VK (текст и фото)
- Настройки VK-токена и группы в личном кабинете
- Статистика подписчиков VK

## Быстрый старт (локально)

```bash
git clone https://github.com/maxmineew/SMM-expert-with-AI.git
cd SMM-expert-with-AI
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
copy config.example.py config.py   # Windows
# cp config.example.py config.py   # Linux / macOS
```

Заполните `config.py`:

- `gigachat_credentials` — ключ из [Sber Developer Studio](https://developers.sber.ru/studio)
- `vk_api_key`, `vk_group_id` — опционально (можно указать в Settings после регистрации)

```bash
python main.py
```

Откройте http://127.0.0.1:5000 — зарегистрируйтесь и войдите.

## Деплой (Render / Railway / VPS)

1. Скопируйте `config.example.py` → `config.py` на сервере и заполните ключи.
2. Установите зависимости: `pip install -r requirements.txt`
3. Запуск через Gunicorn:

```bash
gunicorn main:app --bind 0.0.0.0:$PORT
```

Для PaaS с `Procfile` достаточно подключить репозиторий — стартовая команда уже задана.

Переменные окружения (опционально):

| Переменная | Описание |
|------------|----------|
| `PORT` | Порт сервера (по умолчанию 5000) |
| `SECRET_KEY` | Секрет Flask для сессий |
| `FLASK_DEBUG` | `1` — режим отладки |

## VK: токен для автопоста с фото

Для публикации **с изображением** нужен пользовательский токен с правами `wall`, `photos`, `groups`. Ключ сообщества подходит только для текста.

## Структура проекта

```
app/                  — Flask-приложение, шаблоны, авторизация
generators/           — GigaChat: текст и изображения
social_publishers/    — Публикация в VK
social_stats/         — Статистика VK
static/generated/     — Сгенерированные изображения (не в git)
config.py             — секреты (не в git, создать из config.example.py)
```

## Лицензия

Учебный проект (ZeroCoder, Промпт-инжиниринг 3.0).
