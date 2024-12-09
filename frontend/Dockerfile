FROM node:22-bullseye-slim as build-stage

WORKDIR /app

# envsubst
RUN apt-get update && apt-get install -y gettext-base

COPY frontend/package*.json /app/
RUN npm install --omit=dev
COPY proto /proto
COPY frontend/ /app

RUN npm run build

EXPOSE 3000

ENTRYPOINT sh entrypoint.sh
