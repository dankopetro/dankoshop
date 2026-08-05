FROM node:20-slim AS base
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate

FROM base AS deps
WORKDIR /app
COPY medusa-backend/package.json medusa-backend/pnpm-lock.yaml medusa-backend/turbo.json ./
COPY medusa-backend/pnpm-workspace.yaml ./
COPY medusa-backend/apps/backend/package.json ./apps/backend/
RUN pnpm install --frozen-lockfile

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY medusa-backend/ ./
RUN pnpm build

FROM node:20-slim AS runner
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/apps/backend/.medusa/server ./server
COPY --from=builder /app/apps/backend/node_modules ./node_modules
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 9000
CMD ["node", "server/src/main.js"]
