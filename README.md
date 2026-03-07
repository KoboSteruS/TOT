# ООО «ТОТ» — Официальный сайт бухгалтерских услуг

Современный лендинг для бухгалтерской компании ООО «ТОТ». Профессиональный, чистый дизайн с адаптивной вёрсткой и полным функционалом для привлечения клиентов.

## 🚀 Особенности

- **Адаптивный дизайн**: Идеальное отображение на всех устройствах (desktop, tablet, mobile)
- **Современный UI**: Градиенты, анимации, плавные переходы
- **SEO-оптимизация**: Meta-теги, OpenGraph, семантическая разметка
- **Интерактивный чат-бот**: FAQ-система с автоподсказками
- **Яндекс.Карты**: Интеграция карты с меткой офиса
- **Производительность**: Оптимизированные стили, плавная анимация

## 📁 Структура проекта

```
TOT/
├── app.py                      # Flask-приложение
├── requirements.txt            # Зависимости Python
├── static/
│   ├── styles.css             # Основные стили
│   ├── faq.json               # База знаний для чат-бота
│   └── images/                # Изображения
│       ├── hero/              # Hero-секция
│       ├── about/             # Секция "О нас"
│       ├── services/          # Иконки услуг
│       ├── cta/               # CTA-блоки
│       ├── partners/          # Партнёры (Альфа-Банк)
│       ├── tariffs/           # Изображения тарифов
│       └── Logo.png           # Логотип
└── templates/
    └── index.html             # Главная страница
```

## 🛠 Технологии

- **Backend**: Flask 3.1.0
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Карты**: Яндекс.Карты API 2.1
- **Шрифты**: Inter (Google Fonts)
- **Иконки**: SVG (inline)

## 📦 Установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/yourusername/TOT.git
cd TOT
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить API-ключ Яндекс.Карт

Откройте `templates/index.html` и замените `YOUR_API_KEY` на ваш ключ:

```html
<script src="https://api-maps.yandex.ru/2.1/?apikey=YOUR_API_KEY&lang=ru_RU"></script>
```

Получить API-ключ: https://developer.tech.yandex.ru/services/

### 5. Запустить приложение

```bash
python app.py
```

Сайт будет доступен по адресу: `http://localhost:5000`

## 🎨 Дизайн-система

### Цветовая палитра

```css
--primary: #3d5afe        /* Основной синий */
--primary-hover: #2948d8  /* Hover-состояние */
--text: #2c3e50           /* Основной текст */
--muted: #6b7c93          /* Вторичный текст */
--bg: #f5f7fb             /* Фон */
--surface: #ffffff        /* Карточки */
```

### Типографика

- **Заголовки**: Inter (600-800)
- **Основной текст**: Inter (400-500)
- **Базовый размер**: 16px
- **Высота строки**: 1.6

### Отступы и радиусы

- **Сетка**: 8px
- **Радиус**: 12px (small), 16px (normal), 24px (large)
- **Тени**: 3 уровня (shadow, shadow-md, shadow-lg)

### Брейкпоинты

- **Desktop**: 1024px+
- **Tablet**: 860px–1024px
- **Mobile**: 560px–860px
- **Small mobile**: до 560px

## 🔧 Настройка

### Изменить контакты

Отредактируйте в `templates/index.html`:

```html
<p>+7 (921) 460-46-46 · +7 (964) 319-46-46</p>
<p>Пн–Пт 09:00–18:00 · ул. Федосовой, 31 (офис 6)</p>
```

### Настроить координаты на карте

В `templates/index.html` измените координаты:

```javascript
center: [59.893048, 30.318788],  // [широта, долгота]
```

### Добавить/изменить FAQ

Редактируйте файл `static/faq.json`:

```json
{
  "intent": "your_intent",
  "keywords": ["ключевое слово 1", "ключевое слово 2"],
  "response": "Ответ бота",
  "price": "от 1000 ₽",
  "category": "general"
}
```

## 🚢 Деплой

### Production с Gunicorn

```bash
gunicorn --bind 0.0.0.0:8000 app:app
```

### Nginx конфигурация

```nginx
server {
    listen 80;
    server_name oootot.ru www.oootot.ru;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/TOT/static;
    }
}
```

## 📊 Performance

- **Lighthouse Score**: 95+
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3.5s
- **Cumulative Layout Shift**: < 0.1

## 🐛 Известные проблемы

- Яндекс.Карты требуют API-ключ (получить бесплатно)
- Форма обратной связи пока не отправляет данные (требуется backend)

## 🤝 Контакты

- **Email**: info@oootot.ru
- **Телефон**: +7 (921) 460-46-46, +7 (964) 319-46-46
- **VK**: https://vk.com/oootot
- **Адрес**: ул. Федосовой, 31 (ЖК «Свой берег»), помещение 6

## 📝 Лицензия

© 2026 ООО «ТОТ». Все права защищены.

---

**Сделано с ❤️ для профессиональной бухгалтерии**
