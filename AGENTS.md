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

## Railway Setup (ya creado)
- Proyecto: dankoshop-backend
- Servicios: dankoshop-api (GitHub repo dankopetro/dankoshop), Postgres, Redis
- Login CLI: ya logueado como Dankopetro
- **SOLUCION APLICADA: En Dockerfile se agregó `RUN cp -r /app/medusa-backend/apps/backend/.medusa /app/medusa-backend/.medusa` y en CMD se ejecuta `pnpm exec medusa start`.**

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

## Lo que falta

### Urgente
1. **🔴 Arreglar deploy de Medusa en Railway** - Estado actual:
   - ✅ Build funciona (index.html se genera en apps/backend/.medusa/server/public/admin/index.html)
   - ✅ Migración DB corre
   - ✅ DB connection OK (DATABASE_URL y REDIS_URL seteados)
   - ❌ `medusa start` falla: "Could not find index.html in the admin build directory"
   - **CAUSA RAÍZ**: `medusa start` busca el admin build en `/app/medusa-backend/.medusa/server/public/admin/index.html` pero el build lo genera en `/app/medusa-backend/apps/backend/.medusa/server/public/admin/index.html`
   - **Dockerfile actual**: WORKDIR `/app/medusa-backend/apps/backend` para build y runtime, pero `medusa start` espera ejecutarse desde la raíz del proyecto (`/app/medusa-backend`)

### Lo que se probó (y falló)
| Intento | Qué se hizo | Resultado |
|---------|-------------|-----------|
| 1 | Dockerfile con WORKDIR apps/backend | Build OK, start falla (busca admin en raíz) |
| 2 | WORKDIR raíz, build desde apps/backend | Build falla "medusa not found" |
| 3 | Build desde raíz con `cd apps/backend && pnpm exec medusa build` | Build OK, start falla (busca admin en raíz) |
| 4 | Build en Dockerfile RUN, start en CMD | Build OK, start falla (mismo problema) |
| 5 | WORKDIR apps/backend para todo | Build OK, start falla (busca admin en raíz) |
| 6 | Build en root, start desde apps/backend | Build OK, start falla (mismo problema) |

### Qué probar a continuación (en orden de prioridad)
1. **Opción A - Copiar build output a raíz en Dockerfile RUN** (recomendada):
   ```dockerfile
   RUN cd /app/medusa-backend/apps/backend && NODE_OPTIONS="--max-old-space-size=3072" pnpm exec medusa build 2>&1
   RUN cp -r /app/medusa-backend/apps/backend/.medusa /app/medusa-backend/.medusa
   WORKDIR /app/medusa-backend
   CMD ["sh", "-c", "... && exec ./apps/backend/node_modules/.bin/medusa start"]
   ```

2. **Opción B - Symlink en runtime**:
   ```dockerfile
   CMD ["sh", "-c", "ln -sf /app/medusa-backend/apps/backend/.medusa /app/medusa-backend/.medusa && ..."]
   ```

3. **Opción C - Usar `medusa start --directory` o variable de entorno** (ver docs Medusa v2)

4. **Opción D - Ejecutar todo desde raíz pero con PATH modificado**:
   ```dockerfile
   ENV PATH="/app/medusa-backend/apps/backend/node_modules/.bin:$PATH"
   WORKDIR /app/medusa-backend
   CMD ["sh", "-c", "cd apps/backend && pnpm exec medusa db:migrate && cd .. && exec ./apps/backend/node_modules/.bin/medusa start"]
   ```

### Después (cuando Railway funcione)
2. ❌ Conectar frontend Vercel con backend Railway (fetch a API en vez de products.ts hardcodeado)
3. ❌ Corregir imágenes de productos (muchos productos tienen fotos de otros productos)
4. ❌ Configurar MercadoPago (pagos)
5. ❌ Variables de entorno de Vercel (NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME etc.)
6. ❌ GitHub Actions secrets para CI/CD
7. ❌ Dominio propio

## Imágenes - Estado actual
- **Carpeta products_images/** → 270 SKUs, 744 archivos únicos (sin duplicados por hash)
- **image_urls.json** → 270 SKUs, 744 URLs de Cloudinary
- **CLOUDINARY:** Hay ~951 imágenes subidas (algunas viejas de subidas anteriores que ya no se referencian)
- **PROBLEMA CONOCIDO:** Muchas imágenes pertenecen a productos equivocados (match por timestamp del WhatsApp, no por contenido). El usuario sabe esto y va a revisar manualmente desde el admin de Medusa una vez que esté deployado.

## Estado actual archivos Railway
### Dockerfile (`/home/claudio/Descargas/dankoshop/Dockerfile`)
```dockerfile
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
WORKDIR /app/medusa-backend
RUN NODE_OPTIONS="--max-old-space-size=3072" pnpm exec medusa build 2>&1

EXPOSE 9000
CMD ["sh", "-c", "echo '=== Waiting for DB ===' && sleep 5 && echo '=== Running migration ===' && pnpm exec medusa db:migrate 2>&1 && echo '=== Starting server on 0.0.0.0:9000 ===' && exec ./node_modules/.bin/medusa start"]
```

### railway.toml (`/home/claudio/Descargas/dankoshop/railway.toml`)
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
healthcheckPath = "/store/custom"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[variables]
HOST = "0.0.0.0"
PORT = "9000"
```

## Notas importantes
- El frontend muestra productos HARD CODEADOS en products.ts, NO se conecta al backend todavía
- Las imágenes son de Cloudinary, NO están en el repo
- Medusa v2 usa auth diferente: /auth/user/emailpass (no /admin/auth)
- package.json del backend tiene "packageManager": "pnpm@9.15.9"
- pnpm funciona con Node 22, npm necesita mirror registry (registry.npmmirror.com)
- El .npmrc en la raíz del repo configura el mirror para evitar 429 de npm
- products.ts se genera desde products.json + image_urls.json con script Python
- El script gen_products_ts.py escapa " en nombres y convierte Python None a JS null
- La página /categorias fue creada para arreglar un 404
- El Dockerfile usa Node 20-slim + corepack + pnpm 9.15.9
- Railway project: dankoshop-backend, service: dankoshop-api
- Variables seteadas en Railway: DATABASE_URL, REDIS_URL, HOST, PORT, STORE_CORS, ADMIN_CORS, AUTH_CORS, JWT_SECRET, COOKIE_SECRET, NODE_ENV=production