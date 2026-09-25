FROM node:20-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM alpine:3.20

WORKDIR /dist

COPY --from=build /app/dist /dist

CMD ["sh", "-c", "rm -rf /shared/* && cp -r /dist/. /shared/"]
