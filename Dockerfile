FROM node:20-slim

ENV NODE_OPTIONS="--max-old-space-size=3072"
ENV HOST=0.0.0.0
ENV PORT=9000

RUN corepack enable && corepack prepare pnpm@9.15.9 --activate

WORKDIR /app/medusa-backend

COPY medusa-backend/package.json medusa-backend/pnpm-lock.yaml medusa-backend/pnpm-workspace.yaml medusa-backend/turbo.json medusa-backend/.npmrc ./
COPY medusa-backend/apps/backend/package.json ./apps/backend/
RUN pnpm install --frozen-lockfile

COPY medusa-backend/ ./
RUN NODE_OPTIONS="--max-old-space-size=3072" pnpm build

WORKDIR /app/medusa-backend/apps/backend
EXPOSE 9000
CMD ["sh", "-c", "echo '=== Waiting for DB ===' && sleep 5 && echo '=== Running migration ===' && pnpm exec medusa db:migrate 2>&1 && echo '=== Starting server on 0.0.0.0:9000 ===' && exec ./node_modules/.bin/medusa start"]