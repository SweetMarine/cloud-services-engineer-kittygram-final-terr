FROM nginx:1.22.1

# Генерация самоподписанного сертификата для временного HTTPS
RUN mkdir -p /etc/nginx/ssl \
    && openssl req -x509 -nodes -days 365 \
      -subj "/C=RU/ST=Moscow/L=Moscow/O=Kittygram/OU=IT/CN=_" \
      -newkey rsa:2048 -keyout /etc/nginx/ssl/selfsigned.key \
      -out /etc/nginx/ssl/selfsigned.crt

COPY default.conf /etc/nginx/conf.d/default.conf
