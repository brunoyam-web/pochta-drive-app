# Prerequisites:

## 1. Go get google credentials (see notion)

https://immense-cairnsmore-329.notion.site/fd58c8ee2fef4c7d846e6b33ce15b8bf

## 2. Generate Cert:

If you have any registered domain:

I variant:

1. uncomment respective lines in docker-compose
2. use this command:
```
docker compose run --rm  certbot certonly --webroot \
    --webroot-path /var/www/certbot/ -d api.pochta-app.com
```

II variant:

Inside nginx folder

```
openssl req -x509 -nodes -days 365 \
    -subj "/C=CA/ST=QC/O=Company, Inc./CN=api.pochta-app.com" \
    -addext "subjectAltName=DNS:api.pochta-app.com" \
    -newkey rsa:2048 \
    -keyout ./ssl/private/api.pochta-app.key \
    -out ./ssl/certs/api.pochta-app.crt
```


To launch:
```
docker-compose up --build
```


# **Endpoints**

## GET /auth

Получение ссылки на авторизацию

## POST /auth

Авторизует пользователя в системе. Происходит отмен авторизационного кода, который получен от гугла на пару refresh и access token.

```
body: {
	url: “state=qQoOWXJDqUx9sN3mOcRGCGHNq1kLEJ&code=4/0AfgeXvv4Hu6znCxdsAM6fedz76eFZILBhoynomfSP6ZH7-Zj-kDyU12XJMozFuvIlIFszQ&scope=https://www.googleapis.com/auth/drive”
}
```

response:

```
{
	displayName: string,
	picture: string, // link
	email: string
}
```

Клиент хранит в state эти данные (код работает в пределах одной сессии)

берется из строки редиректа:

```
state=qQoOWXJDqUx9sN3mOcRGCGHNq1kLEJ&code=4/0AfgeXvv4Hu6znCxdsAM6fedz76eFZILBhoynomfSP6ZH7-Zj-kDyU12XJMozFuvIlIFszQ&scope=https://www.googleapis.com/auth/drive.metadata.readonly
```

Регулярка:
```
state=(.*)&code=(4\/.*)&scope=(.*)
```

## GET /files

Ручка выводит все файлы с сервисного аккаунта и/или множества аккаунтов, имеющихся в пользовании нашего приложения

Почта юзера отправляется в хедере запроса X-User-Email

По ней берется refresh token из БД и выполняются операции

response:

```
{
  name: string
  type: string         // "image/jpeg" и другие
  fileId: string       // id файла, который дает google
  downloadUrl: string  // сслыка на скачивание
  priviewUrl: string   // ссылка на предпросмотр
}[]
```

При обращении к гугл диску использовать get и дополнительно написать fields как на скрине (чтобы получить ссылки на скачивание (webContentLink) и просмотр:

## POST /copy

Копирует на гугл диск пользователя файл. В теле, которое возвращается на клиент, приезжает от 1 до 2 новых ссылок на скачку/ просмотр файла, который запрашивался.

request:

```
headers:
- X-User-Email: string

body: {
	fileId: string
}
```

response:

```
data: {
	previewUrl: string
	downloadUrl?: string
}
```

## POST /share

Копирует на гугл сервисный диск файл. В теле, которое возвращается на клиент, приезжает от 1 до 2 новых ссылок на скачку/ просмотр файла, который запрашивался.

request:

```
headers:
- X-User-Email: string

body: {
	fileId: string
}
```

response:

```
data: {
	previewUrl: string
	downloadUrl?: string
}
```
