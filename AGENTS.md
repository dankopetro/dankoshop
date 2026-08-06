# DankoShop - Project Context

## Qué es esto
Ecommerce para vender productos (tecnología, electrodomésticos, outdoor, etc.) con precios mayoristas.
Categorías: Celulares, TVs, Lavarropas, Heladeras, Bicicletas, Gaming, Herramientas, etc.
114 productos, 16 categorías, precios con 4 tipos (lista, efectivo, transferencia, mayorista).

## Arquitectura
```
dankoshop/
├── storefront/          → Next.js 16 + Tailwind (frontend público)
│   ├── src/app/         → Páginas (App Router)
│   │   ├── page.tsx     → Home
│   │   ├── productos/   → Catálogo con búsqueda/filtro
│   │   ├── categorias/  → Listado de categorías
│   │   ├── categoria/   → Productos por categoría (SSG)
│   │   └── producto/    → Detalle de producto con galería
│   ├── src/components/  → header, footer, product-image (zoom/modal)
│   └── src/data/        → products.ts (114 productos + 16 categorías, hardcodeados)
├── medusa-backend/      → MedusaJS v2.18 (admin de productos, pedidos, pagos)
│   └── apps/backend/    → Backend principal
├── scripts/             → Scripts Python (sync, seed, parse_chat, upload_cloudinary, dedup_images)
├── data/                → products.json, image_urls.json, organized_images/, products_images/
├── excel/               → Excel maestro de productos
├── Dockerfile           → Docker build para Railway (Node 20 + pnpm)
└── railway.toml         → Config Railway (DOCKERFILE builder)
```

## Tech Stack
- **Frontend:** Next.js 16, React 19, Tailwind CSS 4, lucide-react
- **Backend:** MedusaJS v2.18, Node.js 22, PostgreSQL 16, Redis 7
- **Imágenes:** Cloudinary (cloud_name: xjuisove, api_key: 645939449555487)
- **Hosting frontend:** Vercel (https://dankoshop-storefront.vercel.app, redirige desde dankoshop.vercel.app)
- **Hosting backend:** Railway (https://railway.com/project/43f44001-29b4-4bf8-ac5b-faceff49a9dc) - **EN PROCESO**
- **DB:** Docker local (dankoshop-postgres, dankoshop-redis en network dankoshop-net)
- **Package manager:** pnpm 9.15.9 (monorepo con pnpm-workspace.yaml)

## Docker Containers
- `dankoshop-postgres` → localhost:5432, user: dankoshop, pass: dankoshop, db: dankoshop
- `dankoshop-redis` → localhost:6379

## Medusa Backend (local)
- Puerto: 9000
- Admin URL: http://localhost:9000/app
- Admin credentials: admin@dankoshop.com / supersecret
- Auth API: POST /auth/user/emailpass (Medusa v2, NO /admin/auth)
- DB migrate: `pnpm exec medusa db:migrate`
- Seed: `python3 scripts/seed.py`
- Arrancar: `nvm use 22 && cd medusa-backend && pnpm exec medusa develop`

## Node.js Versions
- **System:** v18.19.1 (NO usar para nada)
- **nvm v20.20.2:** Para storefront (Vercel build usa Node 20)
- **nvm v22.17.1:** Para medusa-backend (pnpm)
- Siempre usar `nvm use 20` o `nvm use 22` antes de ejecutar comandos

## npm Registry Mirror
El .npmrc en la raíz configura `registry=https://registry.npmmirror.com` para evitar errores 429 de npm. Para medusa-backend usar pnpm (no npm).

## Commands útiles
```bash
# Frontend (Node 20)
nvm use 20 && cd storefront && npm run build
nvm use 20 && cd storefront && npm run dev

# Backend (Node 22 + pnpm)
nvm use 22 && cd medusa-backend && pnpm exec medusa develop

# Docker
docker ps
docker exec dankoshop-postgres psql -U dankoshop -d dankoshop -c "SELECT 1;"

# Upload imágenes a Cloudinary
python3 scripts/upload_cloudinary.py

# Dedup imágenes
python3 scripts/dedup_images.py

# Seed productos a Medusa
python3 scripts/seed.py

# Generar products.ts desde products.json + image_urls.json
python3 /tmp/gen_products_ts.py  # (script temporal, copiar a scripts/ si se necesita permanente)
```

## Variables de entorno
### Frontend (Vercel)
No tiene variables de entorno configuradas todavía.

### Backend local (.env)
```
DATABASE_URL=postgresql://dankoshop:dankoshop@localhost:5432/dankoshop
REDIS_URL=redis://localhost:6379
JWT_SECRET=super-secret-jwt-change-in-production
COOKIE_SECRET=super-secret-cookie-change-in-production
```

### Backend Railway (.env template en medusa-backend/apps/backend/.env.template)
```
DATABASE_URL=postgresql://...  (Railway genera esto)
REDIS_URL=redis://...          (Railway genera esto)
STORE_CORS=https://dankoshop-storefront.vercel.app,http://localhost:3000
ADMIN_CORS=http://localhost:9000,http://localhost:7001
AUTH_CORS=https://dankoshop-storefront.vercel.app,http://localhost:3000,http://localhost:9000
JWT_SECRET=<random>
COOKIE_SECRET=<random>
NODE_ENV=production
```

## GitHub
- Repo: https://github.com/dankopetro/dankoshop
- User: dankopetro (dankopetro@hotmail.com)
- Branch: main
- Railway project: dankoshop-backend (https://railway.com/project/43f44001-29b4-4bf8-ac5b-faceff49a9dc)

## Railway Setup (COMPLETADO Y ONLINE)
- Proyecto: dankoshop-backend
- Servicios: dankoshop-api (GitHub repo dankopetro/dankoshop), Postgres, Redis
- URL Backend: https://dankoshop-api-production.up.railway.app
- Admin Dashboard URL: https://dankoshop-api-production.up.railway.app/app
- **ESTADO: ✅ ONLINE y funcionando correctamente.**

## Lo que está hecho
1. ✅ Parser de chat de WhatsApp (scripts/parse_chat.py)
2. ✅ 114 productos parseados con precios e imágenes
3. ✅ Excel con productos (data/productos_dankoshop.xlsx)
4. ✅ Frontend Next.js desplegado en Vercel
5. ✅ Imágenes únicas en Cloudinary (558 imágenes, sin duplicados entre productos)
6. ✅ Páginas: home, productos, categorías, categoría, detalle con zoom/modal
7. ✅ Medusa backend funcionando local con 113 productos
8. ✅ Docker PostgreSQL + Redis corriendo
9. ✅ products.ts con 114 productos + 16 categorías (export `categories` incluido)
10. ✅ Build de Next.js pasa local y en Vercel (fix de `categories` export + quotes escaping + None→null)
11. ✅ **Backend Medusa v2 desplegado y ONLINE en Railway** (`https://dankoshop-api-production.up.railway.app`)

## Solución del Deploy en Railway (COMPLETADO)
El despliegue de Medusa en Railway presentaba dos problemas principales:

1. **Admin Build Output (Causa Raíz):**
   - `@medusajs/admin-bundler` busca los archivos compilados del Dashboard Admin en `./public/admin` respecto al `rootDirectory` detectado por Medusa.
   - `medusa build` en el monorepo generaba los archivos en `/app/medusa-backend/apps/backend/.medusa/server/public/admin/index.html`.
   - **Solución:** Se agregaron comandos en el `Dockerfile` para copiar la salida del build de admin (`public` y `.medusa`) a todas las rutas posibles del proyecto (`apps/backend/public`, `/app/medusa-backend/public` y `/app/medusa-backend/.medusa`), garantizando que cualquier proceso de Medusa encuentre `index.html`.

2. **Health Check Endpoint (`railway.toml`):**
   - La ruta configurada previamente (`/store/custom`) requería la cabecera `x-publishable-api-key`, devolviendo `HTTP 400 Bad Request` a Railway.
   - **Solución:** Se actualizó `healthcheckPath = "/health"` en `railway.toml`, el cual retorna `HTTP 200 OK`.

---

## Pasos para finalizar el proyecto (Roadmap)

### Paso 1: Cargar catálogo inicial de datos en la DB de Railway (Seed)
- Ejecutar el script `seed.py` configurado apuntando a la base de datos PostgreSQL de producción en Railway (`DATABASE_URL`).
- Verificar que los 114 productos y categorías queden cargados en el backend de Railway.

### Paso 2: Conectar el Frontend en Vercel con el Backend en Railway
- Configurar en Vercel la variable de entorno:
  `NEXT_PUBLIC_MEDUSA_BACKEND_URL=https://dankoshop-api-production.up.railway.app`
- Modificar las páginas del storefront (`src/app/productos`, `src/app/categoria`, etc.) para consultar la API pública de Medusa en lugar de importar `products.ts` hardcodeado.

### Paso 3: Revisión y corrección manual de imágenes
- Acceder al Panel de Administración de Medusa: [https://dankoshop-api-production.up.railway.app/app](https://dankoshop-api-production.up.railway.app/app)
- Credenciales: `admin@dankoshop.com` / `supersecret`.
- Revisar y reasignar las imágenes de los productos que requieran ajuste manual.

### Paso 4: Integración de la pasarela de pagos (MercadoPago)
- Instalar el módulo de pagos de MercadoPago (`@medusajs/payment-mercadopago` o proveedor correspondiente).
- Configurar las variables en Railway:
  - `MERCADOPAGO_ACCESS_TOKEN`
  - `MERCADOPAGO_PUBLIC_KEY`
  - `MERCADOPAGO_WEBHOOK_SECRET`

### Paso 5: Publicación final y Dominio propio
- Configurar las variables de entorno definitivas de producción (Cloudinary, JWT, Cookies secrets).
- Configurar el dominio custom del cliente en Vercel y Railway.

---

## Estado actual de los archivos de Railway

### Dockerfile (`/home/claudio/Descargas/dankoshop/Dockerfile`)
```dockerfile
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

# 2. Copy source and build FROM apps/backend
COPY medusa-backend/ ./
WORKDIR /app/medusa-backend/apps/backend
RUN NODE_OPTIONS="--max-old-space-size=3072" pnpm exec medusa build 2>&1
RUN cp -r /app/medusa-backend/apps/backend/.medusa/server/public /app/medusa-backend/apps/backend/public
RUN cp -r /app/medusa-backend/apps/backend/.medusa/server/public /app/medusa-backend/public
RUN cp -r /app/medusa-backend/apps/backend/.medusa /app/medusa-backend/.medusa

# 3. Runtime from apps/backend
EXPOSE 9000
CMD ["sh", "-c", "echo '=== Waiting for DB ===' && sleep 5 && echo '=== Running migration ===' && pnpm exec medusa db:migrate 2>&1 && echo '=== Starting server on 0.0.0.0:9000 ===' && exec pnpm exec medusa start"]
```

### railway.toml (`/home/claudio/Descargas/dankoshop/railway.toml`)
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
# NO startCommand - let Dockerfile CMD handle it
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[variables]
HOST = "0.0.0.0"
PORT = "9000"
```

## Notas importantes
- El frontend en Vercel muestra productos hardcodeados en `products.ts` de forma provisional.
- Las imágenes están alojadas en Cloudinary.
- Medusa v2 usa autenticación en `/auth/user/emailpass`.
- package.json del backend utiliza `packageManager`: `pnpm@9.15.9`.
- Railway project: `dankoshop-backend`, service: `dankoshop-api`.
- Backend URL activa: `https://dankoshop-api-production.up.railway.app`
- Admin Dashboard URL activa: `https://dankoshop-api-production.up.railway.app/app`