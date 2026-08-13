FROM node:20-slim

ENV NODE_OPTIONS="--max-old-space-size=3072"
ENV HOST=0.0.0.0
ENV PORT=9000

RUN corepack enable && corepack prepare pnpm@9.15.9 --activate

# 1. Install workspace deps at root
WORKDIR /app/medusa-backend
COPY medusa-backend/package.json medusa-backend/pnpm-lock.yaml medusa-backend/pnpm-workspace.yaml medusa-backend/turbo.json medusa-backend/.npmrc ./
COPY medusa-backend/apps/backend/package.json ./apps/backend/
RUN pnpm install --frozen-lockfile

# 2. Copy source and build FROM apps/backend (where medusa CLI lives and build output goes)
COPY medusa-backend/ ./
WORKDIR /app/medusa-backend/apps/backend
RUN NODE_OPTIONS="--max-old-space-size=3072" pnpm exec medusa build --no-lint 2>&1
RUN cp -r /app/medusa-backend/apps/backend/.medusa/server/public /app/medusa-backend/apps/backend/public
RUN cp -r /app/medusa-backend/apps/backend/.medusa/server/public /app/medusa-backend/public
RUN cp -r /app/medusa-backend/apps/backend/.medusa /app/medusa-backend/.medusa

# 3. Runtime from apps/backend (where medusa start expects to run)
EXPOSE 9000
CMD ["sh", "-c", "echo '=== Waiting for DB ===' && sleep 5 && echo '=== Running migration ===' && pnpm exec medusa db:migrate 2>&1 && echo '=== Creating admin user ===' && pnpm exec medusa user --email admin@dankoshop.com --password supersecret 2>&1 || true && echo '=== Increasing prices by 10% ===' && pnpm exec medusa exec increase-prices.cjs 2>&1 && echo '=== Starting server on 0.0.0.0:9000 ===' && exec ./node_modules/.bin/medusa start"]
