FROM node:18-alpine AS builder

WORKDIR /app

COPY ./frontend/customer-portal/package.json ./
RUN npm install --legacy-peer-deps

COPY ./frontend/customer-portal/. .
RUN NODE_OPTIONS=--max_old_space_size=1536 npm run build

FROM nginx:alpine AS final

COPY --from=builder /app/build /usr/share/nginx/html

RUN printf 'server {\n\
    listen 80;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
