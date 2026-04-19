# Kittygram: Проектная работа по облачным сервисам

> **Проектная работа курса "DevOps-инженер облачных сервисов"**  
> Создание виртуальной инфраструктуры для веб-приложения Kittygram с использованием Terraform, Docker и CI/CD

## 📋 О проекте

Kittygram — это веб-приложение для любителей кошек, позволяющее пользователям делиться фотографиями своих питомцев и их достижениями. Проект демонстрирует полный цикл DevOps: от создания инфраструктуры с помощью Terraform до автоматического деплоя через GitHub Actions.

## 🏗️ Архитектура

### Docker образы

Все образы автоматически публикуются в Docker Hub с тегом `latest`:

| Образ                                     | Описание            | Базовый образ | Особенности                         |
| ----------------------------------------- | ------------------- | ------------- | ----------------------------------- |
| `username/kittygram_backend:latest`       | Django приложение   | python:3.10   | Gunicorn, healthcheck на порту 8000 |
| `username/kittygram_frontend:latest`      | React приложение    | node:18       | Production build, http-server       |
| `username/kittygram_gateway:latest`       | Nginx reverse proxy | nginx:1.22.1  | Шаблонизация конфигурации           |

### Docker Compose сервисы

| Сервис          | Порты           | Волюмы                            | Зависимости                     |
| --------------- | --------------- | --------------------------------- | ------------------------------- |
| postgres        | 5432:5432       | pg_data:/var/lib/postgresql/data  | -                               |
| backend         | 8000 (internal) | static, media                     | postgres (healthy)              |
| frontend        | 3000 (internal) | frontend_dist                     | -                               |
| gateway         | 80:80, 443:443  | frontend_dist, static, media      | backend, frontend                |

## 🚀 CI/CD Pipeline

### Основной workflow (deploy.yml)

1. **Matrix · Check PEP8** — параллельный прогон линтеров на нескольких версиях Python  
   _2 джобы, суммарно < 30 сек.; жесткое соблюдение стиля гарантировано еще до сборки образа._

2. **Push to DockerHub** — сборка Docker-образов, тегирование по `SHA`-коммиту и публикация  
   _~ 2 мин. 09 сек.; выводимое имя тега совпадает с коротким хэшем, что упрощает traceability._

3. **Deploy to remote server** — выкладка на удаленный VPS через `scp` + `ssh`  
   _~ 5 мин. 55 сек.; запускаются миграции БД, перезапускаются сервисы, проверяются health-probes._

4. **Run Auto Tests** — быстрый smoke-suite, который стреляет по свежему продовому URL  
   _9 сек. - и ты точно знаешь, что endpoints отвечают 200 OK, а не 502 Bad Gateway._

5. **Send Message to Telegram** — бот публикует зеленый отчет  
   _10 сек. на форматирование, и команда уже хлопает в ладоши в общем чате._

### Terraform workflow (terraform.yml)

Запускается вручную через `workflow_dispatch` с выбором действия:

- `plan` — просмотр планируемых изменений (~30 сек.)
- `apply` — применение изменений (~2-3 мин. для новой инфраструктуры)
- `destroy` — удаление инфраструктуры (~1-2 мин.)

## 📱 Уведомления

### Telegram-бот KittyBot

После успешного деплоя отправляется сообщение с информацией:

- Статус деплоя
- Автор коммита
- Сообщение коммита
- Ссылка на коммит в GitHub

## 🔍 Мониторинг и Health Checks

### Docker Compose Health Checks

| Сервис          | Команда проверки                                    | Интервал | Таймаут | Повторные попытки |
| --------------- | --------------------------------------------------- | -------- | ------- | ----------------- |
| postgres        | pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}    | 10 сек.  | 5 сек.  | 5                 |
| backend         | Python socket check на localhost:8000               | 10 сек.  | 5 сек.  | 5                 |

### Endpoints для мониторинга

- **Основное приложение**: `http://your-server-ip/`
- **Админ-панель Django**: `http://your-server-ip/admin/`
- **API Root**: `http://your-server-ip/api/`
- **Статические файлы**: `http://your-server-ip/static/`
- **Медиа файлы**: `http://your-server-ip/media/`

### Nginx маршрутизация

| Location                 | Proxy Pass                        | Особенности             |
| ------------------------ | --------------------------------- | ----------------------- |
| /api/                    | http://backend:8000/api/          | API endpoints           |
| /admin/                  | http://backend:8000/admin/        | Django admin            |
| /media/                  | /var/html/media/                  | Загруженные изображения |
| /static/admin/           | /var/html/static/admin/           | Статика админки         |
| /static/rest_framework/  | /var/html/static/rest_framework/  | DRF статика             |
| /                        | /usr/share/nginx/html/            | React приложение        |

## 🔌 API Endpoints

### Аутентификация

| Метод | Endpoint           | Описание                          |
| ----- | ------------------ | --------------------------------- |
| POST  | /api/users/        | Регистрация пользователя          |
| POST  | /api/token/login/  | Получение токена                  |
| POST  | /api/token/logout/ | Выход из системы                  |
| GET   | /api/users/me/     | Информация о текущем пользователе |

### Котики

| Метод  | Endpoint            | Описание                              |
| ------ | ------------------- | ------------------------------------- |
| GET    | /api/cats/?page={n} | Список всех котиков (пагинация по 10) |
| POST   | /api/cats/          | Добавление нового котика              |
| GET    | /api/cats/{id}/     | Информация о котике                   |
| PATCH  | /api/cats/{id}/     | Обновление информации                 |
| DELETE | /api/cats/{id}/     | Удаление котика                       |

#### Формат данных котика:

```json
{
  "id": 1,
  "name": "Мурзик",
  "color": "#FFA500",  // При отправке - HEX код, в ответе - название "orange"
  "birth_year": 2020,
  "age": 5,  // Вычисляется автоматически (текущий год - birth_year)
  "owner": 1,  // Read-only, устанавливается автоматически из токена
  "image": "data:image/jpeg;base64,...",  // Base64 encoded
  "achievements": [
    {
      "id": 1,
      "achievement_name": "Мышелов"
    }
  ]
}
```

### Достижения

| Метод  | Endpoint                | Описание               |
| ------ | ----------------------- | ---------------------- |
| GET    | /api/achievements/      | Список всех достижений |
| POST   | /api/achievements/      | Добавление достижения  |
| GET    | /api/achievements/{id}/ | Детали достижения      |
| PUT    | /api/achievements/{id}/ | Обновление достижения  |
| DELETE | /api/achievements/{id}/ | Удаление достижения    |

## ⚙️ Переменные окружения

### Обязательные переменные

```bash
# === PostgreSQL ===
POSTGRES_DB=kittygram_db
POSTGRES_USER=django_user
POSTGRES_PASSWORD=django_password

# === Django ===
SECRET_KEY=your-secret-key-here

# === Database connection ===
DB_HOST=postgres
DB_PORT=5432
```

### Опциональные переменные

```bash
# === Django settings ===
DEBUG=False        # Не используйте True в production
ALLOWED_HOSTS=*    # Рекомендуется указать конкретные домены

# === Gunicorn ===
WEB_CONCURRENCY=4  # Количество воркеров
```

## 🛠️ Локальная разработка

### Быстрый старт

1. **Клонируйте репозиторий:**
```bash
git clone git@github.com:your-username/cloud-services-engineer-kittygram-final.git
cd cloud-services-engineer-kittygram-final
```

2. **Создайте файл `.env`:**
```bash
cp .env.example .env
# Отредактируйте .env под ваши нужды
```

3. **Запустите контейнеры:**
```bash
docker-compose up -d
```

4. **Выполните миграции:**
```bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --noinput
```

5. **Откройте приложение:**
```
http://localhost
```

### Продакшн-запуск

Для продакшна используется файл `docker-compose.production.yml`. CI/CD процесс автоматически деплоит приложение на сервер при пуше в ветку `main`.

## 🧪 Тестирование

### Автотесты

В корне репозитория создайте файл `tests.yml`:

```yaml
repo_owner: your-github-username
kittygram_domain: http://your-server-ip:9000
dockerhub_username: your-dockerhub-username
```

### Локальный запуск тестов

```bash
# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установите зависимости
pip install -r backend/requirements.txt

# Запустите тесты
pytest
```

## 📁 Структура проекта

```
kittygram-final/
├── .env.example                    # Файл с переменными окружения для примера
├── README.md
├── .github/
│   └── workflows/
│       ├── terraform.yml          # Workflow для развёртывания инфраструктуры
│       └── deploy.yml             # Workflow для деплоя приложения
├── infra/                         # Файлы Terraform, описывающие инфраструктуру
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   └── cloud-init.yml
├── backend/                       # Код бэкенда Kittygram
│   ├── README.md
│   ├── cats/
│   ├── kittygram_backend/
│   ├── manage.py
│   └── requirements.txt
├── docker-compose.production.yml  # Docker Compose для продакшна
├── frontend/
│   ├── Dockerfile
│   ├── README.md
│   ├── package.json
│   └── src/
├── kittygram_workflow.yml         # Workflow-файл для проверки ревьюером
├── nginx/                         # Файлы для сборки gateway
│   ├── Dockerfile
│   └── nginx.conf
├── pytest.ini
├── tests.yml                      # Файл с данными для проверки
└── tests/                         # Автотесты
```

## ✅ Чек-лист для проверки

- [x] В репозиторий добавлен workflow для развёртывания инфраструктуры с помощью Terraform
- [x] Проект Kittygram доступен по ссылке, указанной в `tests.yml`
- [x] Стадия автотестов после деплоя выполняется успешно
- [x] Функциональность проекта Kittygram соответствует описанию
- [x] Итоговый состав репозитория соответствует требованиям

---

> **Примечание**: Этот проект создан в рамках курса "DevOps-инженер облачных сервисов" и демонстрирует современные практики CI/CD, контейнеризации и автоматизации развертывания.
