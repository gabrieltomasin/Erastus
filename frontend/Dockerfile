FROM node:22-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV HOSTNAME="0.0.0.0"
COPY --from=builder /app/package.json /app/package-lock.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

# Install nginx for API proxying
RUN apk add --no-cache nginx

COPY nginx.conf /etc/nginx/http.d/default.conf

EXPOSE 3000
COPY start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]
