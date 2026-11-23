# ---------- 构建阶段 ----------
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
# 使用国内镜像源，避免容器内直连 npmjs 超时
RUN npm config set registry https://registry.npmmirror.com && npm install

COPY . .
RUN npm run build

# ---------- 运行阶段 ----------
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
