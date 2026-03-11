# ООО «ТОТ» - Сайт и Админ-панель

Официальный сайт бухгалтерской компании ООО «ТОТ» с мощной админ-панелью для управления контентом.

## 🚀 Возможности

### Публичный сайт
- ✅ Современный дизайн с анимациями
- ✅ Полностью адаптивный (mobile-first)
- ✅ Чат-бот с FAQ
- ✅ Интеграция с Яндекс.Картами
- ✅ Модальные окна для услуг и сертификатов
- ✅ Форма заявки
- ✅ Партнёрство с Альфа-Банком

### Админ-панель
- 🔐 JWT-авторизация через URL
- 📝 Полное управление контентом сайта
- 🤖 Редактор FAQ для чат-бота
- 🖼️ Загрузка и управление изображениями
- ⚡ Современный интерфейс с темной темой
- 📊 Дашборд со статистикой

## 📦 Установка

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd TOT
```

### 2. Создание виртуального окружения
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения
Скопируйте `.env.example` в `.env` и измените значения:
```bash
cp .env.example .env
```

**Важно!** Измените следующие значения в `.env`:
- `JWT_SECRET` - секретный ключ для JWT (используйте случайную строку)
- `ADMIN_TOKEN` - токен для доступа в админку (используйте надёжный токен)
- `SECRET_KEY` - секретный ключ Flask

### 5. Запуск приложения
```bash
python app.py
```

Сайт будет доступен по адресу: http://localhost:5000

## 🔑 Доступ к админ-панели

### Способ 1: Через URL с токеном (рекомендуется)
```
http://localhost:5000/admin/<ваш-ADMIN_TOKEN>
```

Пример:
```
http://localhost:5000/admin/tot-admin-2024-secure-token
```

### Способ 2: Генерация токена (только для разработки)
В режиме разработки можно получить ссылку на админку:
```
http://localhost:5000/api/generate-token
```

## 📖 API Документация

### Авторизация
Все API endpoints требуют JWT токен в заголовке:
```
Authorization: Bearer <jwt-token>
```

### Контент сайта

**Получить весь контент:**
```http
GET /api/content
```

**Обновить контент:**
```http
PUT /api/content
Content-Type: application/json

{
  "company": {...},
  "contacts": {...}
}
```

**Получить/обновить секцию:**
```http
GET /api/content/<section>
PUT /api/content/<section>
```

### FAQ бота

**Получить все FAQ:**
```http
GET /api/faq
```

**Добавить новый FAQ:**
```http
POST /api/faq
Content-Type: application/json

{
  "intent": "new_question",
  "keywords": ["ключевое", "слово"],
  "response": "Ответ бота",
  "category": "general",
  "price": "от 5 000 ₽"
}
```

**Обновить FAQ:**
```http
PUT /api/faq/<index>
```

**Удалить FAQ:**
```http
DELETE /api/faq/<index>
```

### Изображения

**Загрузить изображение:**
```http
POST /api/upload
Content-Type: multipart/form-data

file: <файл>
```

**Список изображений:**
```http
GET /api/images
```

**Удалить изображение:**
```http
DELETE /api/images/<filename>
```

## 📂 Структура проекта

```
TOT/
├── app.py                 # Основное приложение Flask
├── requirements.txt       # Python зависимости
├── .env                   # Переменные окружения (не в git)
├── .env.example          # Пример переменных окружения
├── .gitignore            # Игнорируемые файлы
├── README.md             # Документация
├── static/
│   ├── content.json      # Контент сайта
│   ├── faq.json          # FAQ для чат-бота
│   ├── styles.css        # Стили сайта
│   └── images/           # Загруженные изображения
└── templates/
    ├── index.html        # Главная страница
    └── admin.html        # Админ-панель
```

## 🎨 Возможности админ-панели

### 1. Дашборд
- Статистика по FAQ и изображениям
- Быстрый доступ ко всем разделам

### 2. Контент сайта
- Редактирование информации о компании
- Изменение контактных данных
- Обновление описаний и слоганов

### 3. FAQ бота
- Добавление новых вопросов-ответов
- Редактирование существующих FAQ
- Удаление неактуальных FAQ
- Категоризация по типам
- Добавление цен к услугам

### 4. Изображения
- Drag & Drop загрузка
- Предпросмотр изображений
- Копирование URL изображения
- Удаление изображений

## 🔒 Безопасность

### Рекомендации для production:

1. **Измените все секретные ключи** в `.env`
2. **Не коммитьте `.env` файл** (уже в .gitignore)
3. **Используйте HTTPS** для доступа к админке
4. **Регулярно меняйте** `ADMIN_TOKEN`
5. **Ограничьте доступ** к админ-панели по IP (через nginx/apache)
6. **Отключите** `/api/generate-token` в production (установите `FLASK_ENV=production`)

### Генерация безопасных ключей:

```python
import secrets
print(secrets.token_urlsafe(32))  # Для JWT_SECRET
print(secrets.token_urlsafe(16))  # Для ADMIN_TOKEN
```

## 🚀 Деплой на production

### 1. Через Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 2. Через systemd (Linux)
Создайте файл `/etc/systemd/system/tot.service`:
```ini
[Unit]
Description=TOT Website
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/TOT
Environment="PATH=/var/www/TOT/venv/bin"
ExecStart=/var/www/TOT/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl enable tot
sudo systemctl start tot
```

### 3. Nginx конфигурация
```nginx
server {
    listen 80;
    server_name oootot.ru;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /var/www/TOT/static;
    }
}
```

## 🆘 Поддержка

Если возникли вопросы или проблемы:
- Email: info@tot-ptz.ru
- Телефон: +7 (964) 319-46-46
- ВКонтакте: vk.com/oootot

## 📝 Лицензия

© 2024 ООО «ТОТ». Все права защищены.
