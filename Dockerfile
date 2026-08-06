FROM node:20-slim
RUN corepack enable && corepack prepare pnpm@9.15.9 --activate

WORKDIR /app/medusa-backend

COPY medusa-backend/package.json medusa-backend/pnpm-lock.yaml medusa-backend/pnpm-workspace.yaml medusa-backend/turbo.json medusa-backend/.npmrc ./
COPY medusa-backend/apps/backend/package.json ./apps/backend/
RUN pnpm install --frozen-lockfile

COPY medusa-backend/ ./
RUN pnpm build

WORKDIR /app/medusa-backend/apps/backend
EXPOSE 9000
CMD ["sh", "-c", "npx medusa db:migrate && exec ./node_modules/.bin/medusa start"]