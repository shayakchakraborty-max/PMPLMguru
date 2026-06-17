# Frontend — Next.js 14 (App Router) standalone server. Build context = frontend/ .
# Runs on AWS App Runner / ECS Fargate. Reads BRAIN_URL at runtime (server-side proxies).
FROM node:20-slim AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps
COPY . .
RUN npm run build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000
RUN useradd -m next
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
USER next
EXPOSE 3000
# BRAIN_URL must be set at runtime (App Runner env) -> the /api/* proxies call the brain.
CMD ["node", "server.js"]
