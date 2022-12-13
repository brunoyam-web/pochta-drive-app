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
