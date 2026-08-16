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
│   │   ├── page.tsx     → Home (categorías en vivo de Medusa)
│   │   ├── productos/   → Catálogo con búsqueda/filtro (data en vivo)
│   │   ├── categorias/  → Listado de categorías (en vivo)
│   │   ├── categoria/   → Productos por categoría (en vivo)
│   │   ├── producto/    → Detalle de producto con galería (en vivo)
│   │   ├── admin-contenido/ → Editor de contenido (JSON + GitHub)
│   │   └── api/contenido/route.ts → Guarda contenido vía GitHub API
│   ├── src/components/  → header, footer, product-image (zoom/modal)
│   ├── src/content/     → *.json editables (nosotros, envios, faq, pagos,
│   │                      terminos, privacidad, contacto)
│   └── src/lib/medusa.ts → Cliente Medusa store API (publishable key + ARS)
├── medusa-backend/      → MedusaJS v2.18 (admin de productos, pedidos, pagos)
│   └── apps/backend/    → Backend principal (seed-products.cjs = upsert)
├── scripts/             → Scripts Python (sync_excel v2, seed.py, etc.)
├── data/                → products.json, image_urls.json, organized_images/, products_images/
├── excel/               → Productos_Maestro.xlsx (maestro de precios, versionado)
├── Dockerfile           → Docker build para Railway (Node 20 + pnpm)
└── railway.toml         → Config Railway (DOCKERFILE builder)
```

## Tech Stack
- **Frontend:** Next.js 16, React 19, Tailwind CSS 4, lucide-react
- **Backend:** MedusaJS v2.18, Node.js 22, PostgreSQL 16, Redis 7
- **Imágenes:** Cloudinary (cloud_name: xjuisove, api_key: 645939449555487)
- **Hosting frontend:** Vercel (dankoshop-storefront) - dominio propio https://dankoshop.com.ar
- **Hosting backend:** Railway (https://railway.com/project/43f44001-29b4-4bf8-ac5b-faceff49a9dc) - **ONLINE**
- **DB:** Docker local (dankoshop-postgres, dankoshop-redis en network dankoshop-net)
- **Package manager:** pnpm 9.15.9 (monorepo con pnpm-workspace.yaml)

## Docker Containers
- `dankoshop-postgres` → localhost:5432, user: dankoshop, pass: dankoshop, db: dankoshop
- `dankoshop-redis` → localhost:6379
- Ambos con política `restart: unless-stopped` (se auto-reinician al iniciar Docker/sistema).
  - Ver: `docker inspect dankoshop-postgres --format '{{.HostConfig.RestartPolicy.Name}}'`
  - Aplicar de nuevo si se recrean: `docker update --restart unless-stopped dankoshop-postgres dankoshop-redis`

## Medusa Backend (local)
- Puerto: 9100 (en `.env` local; el storefront local apunta a 9100)
- Admin URL: http://localhost:9100/app
- Admin credentials: admin@dankoshop.com / supersecret
- Publishable key local: `pk_8eee05fa38bf73afe6aa4e6cb494c0a57b01e30aed7533dec018f7fef1e6dcd9`
- Auth API: POST /auth/user/emailpass (Medusa v2, NO /admin/auth)
- DB migrate: `pnpm exec medusa db:migrate`
- Seed: `python3 scripts/seed.py`
- **Arrancar SIEMPRE con el script de control** (evita instancias duplicadas/colgadas):
  - `./scripts/medusa-local.sh start|stop|restart|status`
  - Script: garantiza contenedores arriba, rechaza duplicados en :9100, y `stop` mata
    procesos huérfanos. PID en `/tmp/medusa-local.pid`, log en `/tmp/medusa-local.log`.
- NO levantar `medusa start`/`medusa develop` a mano en varias terminales (causó
  incidente 06/08: 4 instancias, una al 91.8% CPU por DB Docker caída).

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

# Backend (Node 22 + pnpm): levantar SIEMPRE con el script de control
./scripts/medusa-local.sh start    # arranca contenedores + 1 instancia en :9100
./scripts/medusa-local.sh stop     # mata la instancia (aunque esté huérfana)
./scripts/medusa-local.sh status   # contenedores + instancia + memoria
./scripts/medusa-local.sh restart

# Sync Excel → Medusa v2 (REST API)
MEDUSA_BACKEND_URL=http://localhost:9100 python3 scripts/sync_excel_to_medusa_local.py

# Sync contra producción Railway
python3 scripts/sync_excel_to_medusa.py

# Seed upsert de productos (migración Medusa, corre en cada deploy)
# Docker
docker ps
docker exec dankoshop-postgres psql -U dankoshop -d dankoshop -c "SELECT 1;"

# Upload imágenes a Cloudinary
python3 scripts/upload_cloudinary.py

# Dedup imágenes
python3 scripts/dedup_images.py
```

## Regla de precios (syncs de chat nuevos)
Al generar el Excel de sync para un lote nuevo de chat (ej: `preparar_sync_14_15.py`):
- **Precio Compra Mayorista** = precio del mensaje que diga "precio por transferencia 10% descuento (o OFF) por 3 unidades" / "Pagando por transferencia te queda a tan solo Mayorista xxx$ llevando 3 unidades" / "solo dice $xxx Transferencia" / "solo hay un único precio" / "solo precios x1 x6 x12 → tomar el x1" → **× 1,0606**.
- **Precio Venta Bruto** = Precio Compra Mayorista **× 1,072** → es lo que va a Medusa (que aplica 15% y 25%).
- En `Control_14_15_Agosto.xlsx` la col H (Mayorista Efectivo) ya está corregida a mano por el dueño: **col C del sync = col H directa** (no re-aplicar ×1,0606).
- Scripts: `preparar_sync_12_13.py` (formato viejo: Precio Ingresado → Precio Mayorista) y `preparar_sync_14_15.py` (formato nuevo: Precio Compra Mayorista → Precio Venta Bruto). Ambos generan `excel/Nuevos_*_Sync.xlsx` con hoja "Nuevos Sync".

## Variables de entorno
### Frontend (Vercel) - CONFIGURADO
Variables (Settings → Environment Variables, marcar Production+Preview):
```
NEXT_PUBLIC_MEDUSA_BACKEND_URL=https://dankoshop-api-production.up.railway.app
NEXT_PUBLIC_MEDUSA_PUBLISHABLE_KEY=pk_fc06e44a06bc2556affab5c23313b32a8bf5213371a09a482c9479f3ec82fc17
NEXT_PUBLIC_BASE_URL=https://dankoshop.com.ar
GITHUB_TOKEN=<token GitHub con scope repo>          # CONFIGURADO
CONTENT_ADMIN_PASSWORD=<contraseña del editor>       # ej: danko-admin-2026
MERCADOPAGO_ACCESS_TOKEN=<token MP>                  # CONFIGURADO
MERCADOPAGO_PUBLIC_KEY=<public key MP>              # CONFIGURADO
NEXT_PUBLIC_BANCO_TITULAR=CLAUDIO DANIEL MIRANDA
NEXT_PUBLIC_BANCO_NOMBRE=Banco Provincia
NEXT_PUBLIC_BANCO_CUIT=20-18559096-9
NEXT_PUBLIC_BANCO_CBU=0140999803200070892957
NEXT_PUBLIC_BANCO_ALIAS=DANKO.PETRO.GUNTER
```
Hay un script de ayuda: scripts/vercel-env.sh

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
STORE_CORS=https://dankoshop.com.ar,https://www.dankoshop.com.ar,https://dankoshop.vercel.app,http://localhost:3000
ADMIN_CORS=http://localhost:9000,http://localhost:7001
AUTH_CORS=https://dankoshop.com.ar,https://www.dankoshop.com.ar,https://dankoshop.vercel.app,http://localhost:3000,http://localhost:9000
JWT_SECRET=<random>
COOKIE_SECRET=<random>
NODE_ENV=production
```

## GitHub
- Repo: https://github.com/dankopetro/dankoshop
- User: dankopetro (dankopetro@hotmail.com)
- Branch: main
- Railway project: dankoshop-backend (https://railway.com/project/43f44001-29b4-4bf8-ac5b-faceff49a9dc)
- Vercel project: dankoshop-storefront

## Vercel (STOREFRONT ONLINE)
- Proyecto: dankoshop-storefront
- URL producción: https://dankoshop.com.ar (dominio propio, redirige a www)
- Legacy URL: https://dankoshop.vercel.app (redirige al dominio nuevo)
- Env vars configuradas:
  - NEXT_PUBLIC_MEDUSA_BACKEND_URL=https://dankoshop-api-production.up.railway.app
  - NEXT_PUBLIC_MEDUSA_PUBLISHABLE_KEY=pk_fc06e44a06bc2556affab5c23313b32a8bf5213371a09a482c9479f3ec82fc17
  - NEXT_PUBLIC_BASE_URL=https://dankoshop.com.ar
  - CONTENT_ADMIN_PASSWORD=danko-admin-2026
  - MERCADOPAGO_ACCESS_TOKEN / MERCADOPAGO_PUBLIC_KEY / NEXT_PUBLIC_BANCO_* = CONFIGURADOS
  - GITHUB_TOKEN=**CONFIGURADO** (fine-grained, repo dankoshop, Contents: Read and Write — editor /admin-contenido funcional)

## Railway Setup (COMPLETADO Y ONLINE)
- Proyecto: dankoshop-backend
- Servicios: dankoshop-api (GitHub repo dankopetro/dankoshop), Postgres, Redis
- URL Backend: https://dankoshop-api-production.up.railway.app
- Admin Dashboard URL: https://dankoshop-api-production.up.railway.app/app
- Publishable Key: pk_fc06e44a06bc2556affab5c23313b32a8bf5213371a09a482c9479f3ec82fc17
- Región Argentina (ARS): reg_01KZCDHFKD3X8KMZ45NPV8HKZF
- **ESTADO: ✅ ONLINE con 114 productos, metadata de precios, y región ARS.**

## Lo que está hecho
1. ✅ Parser de chat de WhatsApp (scripts/parse_chat.py)
2. ✅ 114 productos parseados con precios e imágenes
3. ✅ Excel con productos (data/productos_dankoshop.xlsx)
4. ✅ Frontend Next.js desplegado en Vercel
5. ✅ Imágenes únicas en Cloudinary (558 imágenes, sin duplicados entre productos)
6. ✅ Páginas: home, productos, categorías, categoría, detalle con zoom/modal
7. ✅ Medusa backend funcionando local con 113 productos
8. ✅ Docker PostgreSQL + Redis corriendo
9. ✅ Backend Medusa v2 desplegado y ONLINE en Railway
10. ✅ Seed upsert de metadata de precios minoristas (efectivo, transferencia, cuotas)
11. ✅ Sync Excel → Medusa v2 (scripts/sync_excel_to_medusa.py) — precios ARS + metadata
12. ✅ Storefront conectado a Medusa en vivo (productos, categorías, búsqueda)
13. ✅ Env vars de Vercel configuradas (Medusa URL, publishable key, admin password)
14. ✅ Editor de contenido /admin-contenido con JSON + GitHub API
15. ✅ Contenido institucional editable (nosotros, envios, faq, pagos, terminos, privacidad, contacto)
16. ✅ Tienda funcionando en producción: dankoshop.vercel.app
17. ✅ Robustez local: contenedores con restart policy + script `scripts/medusa-local.sh`
    (anti-instancias-duplicadas/colgadas) + puerto local unificado en 9100
18. ✅ Checkout online implementado: `/checkout` (MercadoPago + Transferencia CVU), `/comprobante`
    (recibo imprimible), API de preferencia, webhook y registro de pedidos. Falta solo el
    `MERCADOPAGO_ACCESS_TOKEN` + datos banco en Vercel para activar el pago real.
19. ✅ Parser de chat 14-15 agosto (scripts/procesar_chat_14_15.py) → Control_14_15_Agosto.xlsx
    (46 productos: 17 NUEVO, 16 BAJA, 12 SIN SKU, 1 SIN MAYORISTA). Filtrado: dupes, SIN CAMBIO,
    SIN SKU en maestro por nombre, Tupper Gemplast. Normalización Unicode matemático → ASCII.
20. ✅ Sync Excel 14-15 (scripts/preparar_sync_14_15.py) → Nuevos_14_15_Sync.xlsx (28 productos).
    Formato: col C = Precio Compra Mayorista (col H control directa), col F = Precio Venta Bruto
    (C × 1.072). Hoja "Nuevos Sync", 8 columnas, espejo del 12-13.
21. ✅ Footer: teléfono → WhatsApp con icono SVG oficial (#25D366) + enlace wa.me/5492216219596.
22. ✅ Home: fix category card text overflow (overflow-hidden, line-clamp-2, break-words).

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

## Pasos restantes (Roadmap)

### ✅ PASOS COMPLETADOS
- Seed upsert de metadata de precios minoristas
- Sync Excel → Medusa v2 (REST API)
- Conectar storefront a Medusa en vivo
- Configurar env vars de Vercel
- Deploy de Railway con seed automático
- Editor de contenido /admin-contenido

### ✅ Paso 1: GITHUB_TOKEN para el editor (COMPLETADO)
- Token fine-grained con Contents: Read and Write sobre el repo dankoshop
- Configurado como env var `GITHUB_TOKEN` en Vercel
- El editor /admin-contenido guarda cambios directamente al repo (verificado OK)

### Paso 2: Revisión manual de imágenes
- Acceder al Panel de Administración de Medusa: https://dankoshop-api-production.up.railway.app/app
- Credenciales: admin@dankoshop.com / supersecret
- Revisar y reasignar las imágenes de los productos que requieran ajuste manual

### ✅ Paso 3: Pasarela de pagos (MercadoPago) - COMPLETADO
- Implementado el flujo de checkout y comprobantes en el storefront (ver más abajo "Checkout y Pagos").
- Env vars de MercadoPago y banco configuradas en Vercel. Pago real validado.
- Rutas: `/checkout`, `/comprobante`, `/api/mercadopago/preference`, `/api/mercadopago/notification`, `/api/ordenes`.

### ✅ Paso 4: Dominio propio (COMPLETADO)
- Dominio `dankoshop.com.ar` configurado en Vercel (nameservers delegados a Vercel).
- URL producción: https://dankoshop.com.ar (redirige a www).
- `NEXT_PUBLIC_BASE_URL=https://dankoshop.com.ar` actualizado en Vercel.
- Emails con dominio propio: `ventas@dankoshop.com.ar` vía ImprovMX reenviando a Gmail.
- Email también configurado en los otros dominios (pcproducciones.net.ar, cosmovision.net.ar) vía ImprovMX.

## Checkout y Pagos (implementado)
- `POST /api/mercadopago/preference` → crea preferencia (usa `MERCADOPAGO_ACCESS_TOKEN`) y redirige a MP (cubre tarjeta, efectivo, Rapipago/Pago Fácil).
- `POST /api/ordenes` → guarda pedidos en `data/pedidos.json` vía GitHub.
- `POST /api/mercadopago/notification` → webhook marca pedido "pagado" al recibir `payment.approved`.
- `/checkout` → selector de pago (MercadoPago o Transferencia CVU).
- `/comprobante` → recibo imprimible/PDF.
- Datos banco vía env vars: `NEXT_PUBLIC_BANCO_{TITULAR,CBU,ALIAS,CUIT,NOMBRE}`.
- ✅ Env vars Vercel configuradas: `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_PUBLIC_KEY`, `NEXT_PUBLIC_BASE_URL`, datos del banco.

### ✅ Paso 4: Dominio propio (COMPLETADO)
- Dominio `dankoshop.com.ar` configurado en Vercel (nameservers delegados a Vercel).
- URL producción: https://dankoshop.com.ar (redirige a www). `NEXT_PUBLIC_BASE_URL` actualizado.
- Email con dominio propio: `ventas@dankoshop.com.ar` vía ImprovMX → Gmail.

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

## Notas finales
- El storefront en Vercel está conectado a Medusa en vivo (no usa products.ts hardcodeado).
- Las imágenes están alojadas en Cloudinary.
- Medusa v2 usa autenticación en `/auth/user/emailpass`.
- package.json del backend utiliza `packageManager`: `pnpm@9.15.9`.
- Railway project: `dankoshop-backend`, service: `dankoshop-api`.
- Backend URL activa: `https://dankoshop-api-production.up.railway.app`
- Admin Dashboard URL activa: `https://dankoshop-api-production.up.railway.app/app`
- Storefront URL activa: `https://dankoshop.com.ar` (redirige a www)
- Editor de contenido: `https://dankoshop.com.ar/admin-contenido` (contraseña: danko-admin-2026)
- Sync Excel → Medusa: `python3 scripts/sync_excel_to_medusa.py` (producción) o `sync_excel_to_medusa_local.py` (local)
- Precios: web pública muestra solo minorista (efectivo, transferencia, cuotas). Mayorista es interno/admin.
- Email: `ventas@dankoshop.com.ar` (ImprovMX → Gmail).
- Teléfono/WhatsApp: 221 621 9596.