# 🔌 API документация ООО «ТОТ»

## Общее описание

Backend построен на **Flask** и предоставляет REST API для управления контентом сайта, FAQ чат-бота, сертификатами и изображениями.

**Базовый URL**: `http://localhost:5000` (development)  
**Авторизация**: JWT Bearer Token  
**Формат данных**: JSON

---

## 🔐 Авторизация

### JWT Token

Все защищённые эндпоинты требуют JWT-токен в header:

```http
Authorization: Bearer {JWT_TOKEN}
```

### Генерация токена (Development только!)

```http
GET /api/generate-token
```

**Response**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

⚠️ **ВАЖНО**: В production этот эндпоинт должен быть удалён!

### Получение токена для админ-панели

1. Настройте `.env` файл:
```env
ADMIN_TOKEN=your-secret-admin-token
JWT_SECRET=your-jwt-secret-key
```

2. Сгенерируйте JWT через `/api/generate-token` или используйте готовый токен

3. Откройте админ-панель:
```
http://localhost:5000/admin/{JWT_TOKEN}
```

---

## 📄 Публичные эндпоинты

### 1. Главная страница

```http
GET /
```

**Описание**: Рендерит главную страницу сайта (index.html)

**Response**: HTML

---

### 2. Админ-панель

```http
GET /admin/<token>
```

**Параметры**:
- `token` (path) — JWT токен для доступа

**Описание**: Проверяет токен и рендерит админ-панель

**Response**: 
- **200**: HTML (admin.html) с валидным JWT в JS
- **401**: Unauthorized (неверный токен)

**Пример**:
```
GET /admin/eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📝 Content API (Управление контентом сайта)

### 1. Получить весь контент

```http
GET /api/content
```

**Auth**: Требуется JWT

**Response**:
```json
{
  "company": {
    "name": "ООО «ТОТ»",
    "tagline": "Ваша идеальная бухгалтерия",
    ...
  },
  "contacts": { ... },
  "hero": { ... },
  "about": { ... },
  "services": { ... },
  // ... все остальные секции
}
```

**Status Codes**:
- **200**: OK
- **401**: Unauthorized
- **500**: Internal Server Error

---

### 2. Обновить весь контент

```http
PUT /api/content
```

**Auth**: Требуется JWT

**Body** (JSON):
```json
{
  "company": { ... },
  "contacts": { ... },
  ...
}
```

**Response**:
```json
{
  "message": "Content updated successfully"
}
```

**Status Codes**:
- **200**: OK
- **400**: Bad Request (невалидный JSON)
- **401**: Unauthorized
- **500**: Internal Server Error

---

### 3. Получить конкретную секцию

```http
GET /api/content/<section>
```

**Auth**: Требуется JWT

**Параметры**:
- `section` (path) — название секции (company, contacts, hero, about, services, и т.д.)

**Пример**:
```
GET /api/content/hero
```

**Response**:
```json
{
  "kicker": "ООО «ТОТ»",
  "title": "ВАША ИДЕАЛЬНАЯ<br>БУХГАЛТЕРИЯ",
  "description": "...",
  "btn_primary": "Связаться",
  "btn_secondary": "Услуги"
}
```

**Status Codes**:
- **200**: OK
- **404**: Section not found
- **401**: Unauthorized

---

### 4. Обновить конкретную секцию

```http
PUT /api/content/<section>
```

**Auth**: Требуется JWT

**Параметры**:
- `section` (path) — название секции

**Body** (JSON):
```json
{
  "title": "Новый заголовок",
  "description": "Новое описание"
}
```

**Response**:
```json
{
  "message": "Section updated successfully"
}
```

**Status Codes**:
- **200**: OK
- **400**: Bad Request
- **404**: Section not found
- **401**: Unauthorized

---

## 💬 FAQ API (Управление чат-ботом)

### 1. Получить все вопросы

```http
GET /api/faq
```

**Auth**: Требуется JWT

**Response**:
```json
{
  "faq": [
    {
      "intent": "about_company",
      "keywords": ["кто вы", "о вас", "компания"],
      "response": "ООО «ТОТ» работает...",
      "category": "general"
    },
    ...
  ]
}
```

**Status Codes**:
- **200**: OK
- **401**: Unauthorized
- **500**: Internal Server Error

---

### 2. Добавить новый вопрос

```http
POST /api/faq
```

**Auth**: Требуется JWT

**Body** (JSON):
```json
{
  "intent": "new_question",
  "keywords": ["ключ1", "ключ2"],
  "response": "Ответ бота",
  "category": "general",
  "price": "от 5 000 ₽" (опционально)
}
```

**Response**:
```json
{
  "message": "FAQ item added successfully"
}
```

**Status Codes**:
- **201**: Created
- **400**: Bad Request (отсутствуют обязательные поля)
- **401**: Unauthorized
- **500**: Internal Server Error

**Обязательные поля**:
- `intent` (string)
- `keywords` (array)
- `response` (string)
- `category` (string)

---

### 3. Обновить вопрос

```http
PUT /api/faq/<index>
```

**Auth**: Требуется JWT

**Параметры**:
- `index` (path) — индекс вопроса в массиве (начиная с 0)

**Body** (JSON):
```json
{
  "intent": "updated_intent",
  "keywords": ["обновлённые", "ключи"],
  "response": "Обновлённый ответ",
  "category": "services"
}
```

**Response**:
```json
{
  "message": "FAQ item updated successfully"
}
```

**Status Codes**:
- **200**: OK
- **400**: Bad Request
- **404**: FAQ item not found
- **401**: Unauthorized

---

### 4. Удалить вопрос

```http
DELETE /api/faq/<index>
```

**Auth**: Требуется JWT

**Параметры**:
- `index` (path) — индекс вопроса в массиве

**Пример**:
```
DELETE /api/faq/5
```

**Response**:
```json
{
  "message": "FAQ item deleted successfully"
}
```

**Status Codes**:
- **200**: OK
- **404**: FAQ item not found
- **401**: Unauthorized

---

## 🏆 Certificates API (Управление сертификатами)

### 1. Получить все сертификаты

```http
GET /api/certificates
```

**Auth**: Не требуется (публичный эндпоинт для отображения на сайте)

**Response**:
```json
{
  "certificates": [
    {
      "id": "alfa-cert-1",
      "title": "Сертификат партнёра Альфа-Банк",
      "image": "/static/images/partners/alfa-certificate.png",
      "description": "Официальное партнёрство",
      "date": "2024"
    }
  ]
}
```

**Status Codes**:
- **200**: OK
- **500**: Internal Server Error

---

### 2. Добавить новый сертификат

```http
POST /api/certificates
```

**Auth**: Требуется JWT

**Body** (JSON):
```json
{
  "title": "Название сертификата",
  "image": "/static/images/cert.png",
  "description": "Описание",
  "date": "2024"
}
```

**Response**:
```json
{
  "message": "Certificate added successfully",
  "id": "generated-uuid-v4"
}
```

**Status Codes**:
- **201**: Created
- **400**: Bad Request (отсутствуют обязательные поля)
- **401**: Unauthorized

**Обязательные поля**:
- `title` (string)
- `image` (string)

**Опциональные поля**:
- `description` (string, default: "")
- `date` (string, default: "")

---

### 3. Обновить сертификат

```http
PUT /api/certificates/<cert_id>
```

**Auth**: Требуется JWT

**Параметры**:
- `cert_id` (path) — UUID сертификата

**Body** (JSON):
```json
{
  "title": "Обновлённое название",
  "image": "/static/images/new-cert.png",
  "description": "Новое описание",
  "date": "2025"
}
```

**Response**:
```json
{
  "message": "Certificate updated successfully"
}
```

**Status Codes**:
- **200**: OK
- **400**: Bad Request
- **404**: Certificate not found
- **401**: Unauthorized

---

### 4. Удалить сертификат

```http
DELETE /api/certificates/<cert_id>
```

**Auth**: Требуется JWT

**Параметры**:
- `cert_id` (path) — UUID сертификата

**Пример**:
```
DELETE /api/certificates/alfa-cert-1
```

**Response**:
```json
{
  "message": "Certificate deleted successfully"
}
```

**Status Codes**:
- **200**: OK
- **404**: Certificate not found
- **401**: Unauthorized

---

## 🖼️ Images API (Управление изображениями)

### 1. Загрузить изображение

```http
POST /api/upload
```

**Auth**: Требуется JWT

**Content-Type**: `multipart/form-data`

**Body** (Form Data):
- `file` (file) — файл изображения
- `path` (string, опционально) — путь для замены существующего файла

**Пример 1: Загрузка нового изображения**
```
POST /api/upload
Content-Type: multipart/form-data

file: [binary data of image.png]
```

**Response**:
```json
{
  "message": "File uploaded successfully",
  "filename": "image_1678901234.png",
  "url": "/static/images/image_1678901234.png"
}
```

**Пример 2: Замена существующего изображения**
```
POST /api/upload
Content-Type: multipart/form-data

file: [binary data of Logo.png]
path: Logo.png
```

**Response**:
```json
{
  "message": "File replaced successfully",
  "filename": "Logo.png",
  "url": "/static/images/Logo.png"
}
```

**Ограничения**:
- Максимальный размер: 16MB
- Разрешённые форматы: JPG, JPEG, PNG, GIF, SVG, WEBP

**Status Codes**:
- **200**: OK (замена файла)
- **201**: Created (новый файл)
- **400**: Bad Request (нет файла, неверный формат, превышен размер)
- **401**: Unauthorized
- **500**: Internal Server Error

---

### 2. Получить список изображений

```http
GET /api/images
```

**Auth**: Требуется JWT

**Response**:
```json
{
  "images": [
    {
      "name": "Logo.png",
      "url": "/static/images/Logo.png",
      "size": 12345
    },
    {
      "name": "Hero.png",
      "url": "/static/images/Hero.png",
      "size": 67890
    }
  ]
}
```

**Поля**:
- `name` (string) — имя файла
- `url` (string) — относительный URL
- `size` (integer) — размер в байтах

**Status Codes**:
- **200**: OK
- **401**: Unauthorized
- **500**: Internal Server Error

---

### 3. Удалить изображение

```http
DELETE /api/images/<filename>
```

**Auth**: Требуется JWT

**Параметры**:
- `filename` (path) — имя файла (URL-encoded)

**Пример**:
```
DELETE /api/images/old-image.png
```

**Response**:
```json
{
  "message": "Image deleted successfully"
}
```

**Status Codes**:
- **200**: OK
- **404**: Image not found
- **401**: Unauthorized
- **500**: Internal Server Error

---

## 📁 Служебные эндпоинты

### Статические файлы

```http
GET /static/<path:filename>
```

**Описание**: Отдача статических файлов (CSS, JS, изображения)

**Примеры**:
```
GET /static/styles.css
GET /static/images/Logo.png
GET /static/content.json
```

**Response**: Файл (с правильным Content-Type)

**Status Codes**:
- **200**: OK
- **404**: File not found

---

## 🔒 Безопасность

### JWT Verification

Декоратор `@jwt_required` проверяет токен:

```python
@jwt_required
def protected_endpoint():
    # Доступно только с валидным JWT
    pass
```

### Проверка токена

1. Извлечение из header: `Authorization: Bearer {token}`
2. Декодирование с помощью `JWT_SECRET`
3. Проверка срока действия (exp claim)
4. Проверка ADMIN_TOKEN в payload

### Валидация файлов

При загрузке изображений:
1. Проверка расширения файла (`allowed_file`)
2. Проверка размера (<16MB)
3. Безопасное сохранение (`secure_filename` из Werkzeug)

### CORS

По умолчанию CORS отключён. Для включения:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Разрешить все origins (только для development!)
```

Для production:
```python
CORS(app, origins=["https://yourdomain.com"])
```

---

## 🚀 Примеры использования

### Python (requests)

#### Получение контента

```python
import requests

JWT_TOKEN = "your-jwt-token"
headers = {"Authorization": f"Bearer {JWT_TOKEN}"}

response = requests.get("http://localhost:5000/api/content", headers=headers)
content = response.json()
print(content["hero"]["title"])
```

#### Обновление FAQ

```python
import requests

JWT_TOKEN = "your-jwt-token"
headers = {"Authorization": f"Bearer {JWT_TOKEN}"}

new_faq = {
    "intent": "new_question",
    "keywords": ["вопрос", "тест"],
    "response": "Тестовый ответ",
    "category": "general"
}

response = requests.post(
    "http://localhost:5000/api/faq", 
    json=new_faq, 
    headers=headers
)

print(response.json())  # {"message": "FAQ item added successfully"}
```

#### Загрузка изображения

```python
import requests

JWT_TOKEN = "your-jwt-token"
headers = {"Authorization": f"Bearer {JWT_TOKEN}"}

files = {"file": open("logo.png", "rb")}

response = requests.post(
    "http://localhost:5000/api/upload", 
    files=files, 
    headers=headers
)

print(response.json())  # {"filename": "logo_...", "url": "/static/images/..."}
```

---

### JavaScript (Fetch API)

#### Получение FAQ

```javascript
const JWT_TOKEN = 'your-jwt-token';

async function getFaq() {
  const response = await fetch('/api/faq', {
    headers: {
      'Authorization': `Bearer ${JWT_TOKEN}`
    }
  });
  
  const data = await response.json();
  console.log(data.faq);
}

getFaq();
```

#### Добавление сертификата

```javascript
const JWT_TOKEN = 'your-jwt-token';

async function addCertificate() {
  const cert = {
    title: 'Новый сертификат',
    image: '/static/images/cert.png',
    description: 'Описание',
    date: '2024'
  };
  
  const response = await fetch('/api/certificates', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${JWT_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(cert)
  });
  
  const result = await response.json();
  console.log(result.message);
}

addCertificate();
```

#### Загрузка файла

```javascript
const JWT_TOKEN = 'your-jwt-token';

async function uploadImage(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('/api/upload', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${JWT_TOKEN}`
    },
    body: formData
  });
  
  const result = await response.json();
  console.log(result.url);
}

// Использование
const input = document.querySelector('input[type="file"]');
input.addEventListener('change', (e) => {
  uploadImage(e.target.files[0]);
});
```

---

## 📊 Коды ответов (Summary)

| Код | Значение | Когда возвращается |
|-----|----------|-------------------|
| 200 | OK | Успешный GET/PUT/DELETE |
| 201 | Created | Успешный POST (создание ресурса) |
| 400 | Bad Request | Невалидные данные, отсутствуют поля |
| 401 | Unauthorized | Неверный/отсутствующий JWT токен |
| 404 | Not Found | Ресурс не найден |
| 500 | Internal Server Error | Ошибка сервера (JSON parse, file I/O) |

---

## 🐛 Отладка API

### Включение Debug режима

В `app.py`:
```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### Логирование запросов

Добавьте middleware:
```python
@app.before_request
def log_request():
    print(f"{request.method} {request.path}")
    if request.json:
        print(f"Body: {request.json}")
```

### Тестирование эндпоинтов

#### С помощью curl

```bash
# Получить контент
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:5000/api/content

# Добавить FAQ
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"intent":"test","keywords":["test"],"response":"Test","category":"general"}' \
  http://localhost:5000/api/faq

# Загрузить изображение
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@image.png" \
  http://localhost:5000/api/upload
```

#### С помощью Postman

1. Создайте коллекцию "TOT API"
2. Добавьте переменную окружения `JWT_TOKEN`
3. В каждом запросе добавьте header:
   - Key: `Authorization`
   - Value: `Bearer {{JWT_TOKEN}}`
4. Импортируйте все эндпоинты

---

## 🔄 Версионирование API

В будущем можно добавить версионирование:

```python
# API v1
@app.route('/api/v1/content', methods=['GET'])
def get_content_v1():
    # ...

# API v2
@app.route('/api/v2/content', methods=['GET'])
def get_content_v2():
    # Новый формат данных
    # ...
```

---

## 📚 Дополнительные ресурсы

### Flask документация
- [Официальная документация Flask](https://flask.palletsprojects.com/)
- [Flask RESTful](https://flask-restful.readthedocs.io/)

### JWT
- [PyJWT документация](https://pyjwt.readthedocs.io/)
- [JWT.io](https://jwt.io/) — декодер токенов

### Безопасность
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.3.x/security/)

---

## ✅ Заключение

API предоставляет полный контроль над сайтом:
- ✅ Управление контентом (Content API)
- ✅ Управление чат-ботом (FAQ API)
- ✅ Управление сертификатами (Certificates API)
- ✅ Управление изображениями (Images API)
- ✅ JWT-авторизация для безопасности
- ✅ RESTful архитектура
- ✅ JSON формат данных

Все изменения через API **мгновенно отражаются** на сайте, так как данные хранятся в JSON-файлах, которые читаются при каждом запросе.
