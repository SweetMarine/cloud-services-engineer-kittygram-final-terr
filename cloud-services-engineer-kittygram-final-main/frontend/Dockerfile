FROM node:18-alpine as build
WORKDIR /app

COPY package.json package.json
COPY package-lock.json package-lock.json

RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.19
WORKDIR /app

COPY --from=build /app/build /app/build
COPY --from=build /app/build /usr/share/nginx/html

COPY nginx/default.conf /etc/nginx/conf.d/default.conf
