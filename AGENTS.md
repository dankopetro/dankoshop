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
- **Hosting backend:** Railway (https://railway.com/project/43f44001-29b4-4bf8-ac5b-faceff49a9dc) - NO FUNCIONA AÚN
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
- **PROBLEMA: El Dockerfile compila bien pero el server no arranca. `medusa start` no produce ningún log de runtime. Verificar: si el CMD ejecuta medusa start, si DATABASE_URL se pasa correctamente, si el healthcheck path es correcto.**

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
1. **🔴 Arreglar deploy de Medusa en Railway** - El Dockerfile compila pero `medusa start` no arranca. Ideas para probar:
   - Cambiar CMD a `node .medusa/server/src/main.js` o similar
   - Verificar si falta correr `medusa db:migrate` en Railway antes de start
   - Probar con un healthcheck en `/store/custom` en vez de `/`
   - Revisar si las env vars (DATABASE_URL, REDIS_URL) se pasan correctamente al container
   - Copiar `.medusa/` al stage runner en vez de usar `medusa start`

### Después
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
