# 🚀 Guía de Deploy - DankoShop

## Arquitectura Final

```
┌─────────────────┐         ┌──────────────────┐
│   Vercel        │ ──────► │   Railway        │
│   (Frontend)    │  API    │   (Backend + DB) │
│   Next.js 14    │ ◄────── │   Medusa v2      │
│                 │         │   PostgreSQL     │
└─────────────────┘         │   Redis          │
                            └──────────────────┘
```

---

## Paso 1: Deploy Backend en Railway (PRIMERO)

1. Ir a [railway.app/new](https://railway.app/new)
2. Seleccionar **"Deploy from GitHub repo"**
3. Elegir repo `dankopetro/dankoshop`
4. En **"Service Settings"**:
   - Root directory: `medusa-backend`
   - Start command: `npm run start`
5. Agregar **PostgreSQL**:
   - Click en **"+ New"** → **"Database"** → **"PostgreSQL"**
   - Railway crea `DATABASE_URL` automáticamente
6. Agregar **Redis**:
   - Click en **"+ New"** → **"Database"** → **"Redis"**
   - Railway crea `REDIS_URL` automáticamente
7. En **Variables** del servicio, agregar:
   ```
   NODE_ENV=production
   STORE_CORS=https://dankoshop.vercel.app
   ADMIN_CORS=https://dankoshop-backend.up.railway.app
   AUTH_CORS=https://dankoshop.vercel.app,https://dankoshop-backend.up.railway.app
   JWT_SECRET=tu-secret-jwt-muy-seguro
   COOKIE_SECRET=tu-secret-cookie-muy-seguro
   MEDUSA_ADMIN_EMAIL=admin@dankoshop.com
   MEDUSA_ADMIN_PASSWORD=tu-password-seguro
   ```
8. Esperar el deploy (2-3 min)
9. Ir a **Settings → Networking → Generate Domain** → anotar el URL (ej: `https://dankoshop-backend.up.railway.app`)
10. **Migraciones**: En la terminal de Railway, ejecutar:
    ```bash
    npx medusa db:migrate
    ```

---

## Paso 2: Deploy Frontend en Vercel

1. Ir a [vercel.com/new](https://vercel.com/new)
2. Seleccionar **"Import Git Repository"** → `dankopetro/dankoshop`
3. Configurar:
   - **Framework Preset**: Next.js
   - **Root Directory**: `storefront`
   - **Build Command**: `npm run build`
   - **Install Command**: `npm install --legacy-peer-deps`
4. Variables de entorno:
   ```
   NEXT_PUBLIC_MEDUSA_BACKEND_URL=https://tu-backend.railway.app
   NEXT_PUBLIC_BASE_URL=https://tu-dominio.vercel.app
   ```
5. **Deploy** → Esperar 2-3 min
6. Anotar el URL (ej: `https://dankoshop.vercel.app`)

---

## Paso 3: Actualizar CORS en Railway

Una vez que tengas ambos URLs:

1. Volver a Railway → Variables de `dankoshop-backend`
2. Actualizar:
   ```
   STORE_CORS=https://tu-dominio.vercel.app
   AUTH_CORS=https://tu-dominio.vercel.app,https://tu-backend.railway.app
   ```
3. Railway redespliega automáticamente

---

## Paso 4: Importar Productos

Opción A - Desde tu máquina:
```bash
cd dankoshop
export MEDUSA_BACKEND_URL=https://tu-backend.railway.app
export MEDUSA_ADMIN_EMAIL=admin@dankoshop.com
export MEDUSA_ADMIN_PASSWORD=tu-password
python3 scripts/seed.py
```

Opción B - Desde Railway CLI:
```bash
railway login
railway link
railway run python3 scripts/seed.py
```

---

## Paso 5: Configurar MercadoPago (opcional)

1. Crear cuenta en [mercadopago.com.ar](https://mercadopago.com.ar)
2. Ir a **Tus integraciones → Credencias**
3. Copiar **Access Token** y **Public Key**
4. En el proyecto:
   ```bash
   cd medusa-backend/apps/backend
   npm install @medusajs/payment-mercadopago --legacy-peer-deps
   ```
5. Descomentar módulo en `medusa-config.ts`
6. Agregar variables en Railway:
   ```
   MERCADOPAGO_ACCESS_TOKEN=tu-token
   MERCADOPAGO_PUBLIC_KEY=tu-public-key
   ```
7. Commit & push → redeploy automático

---

## Paso 6: Dominio Custom (opcional)

1. Comprar dominio (ej: `dankoshop.com.ar`)
2. En **Vercel**: Settings → Domains → agregar dominio
3. En **Railway**: Settings → Domains → agregar `api.tudominio.com.ar`
4. Configurar DNS:
   - `www` → CNAME a `cname.vercel-dns.com`
   - `api` → CNAME a tu dominio de Railway

---

## ✅ Verificación Final

```bash
# Frontend
curl -I https://dankoshop.vercel.app

# Backend health
curl https://dankoshop-backend.up.railway.app/health

# API productos
curl https://dankoshop-backend.up.railway.app/store/products
```

---

## 🔧 Comandos de Desarrollo Local

```bash
# Base de datos (Docker)
docker start dankoshop-postgres dankoshop-redis

# Backend
cd medusa-backend/apps/backend
cp .env.template .env
npm run dev

# Frontend
cd storefront
npm install --legacy-peer-deps
npm run dev

# Importar productos
python3 scripts/seed.py
```

---

## 📊 Estado Actual

- ✅ Repositorio GitHub configurado
- ✅ 114 productos parseados del chat
- ✅ Medusa backend (PostgreSQL + Redis)
- ✅ Next.js storefront con UI completa
- ✅ Sync script (Excel → Medusa)
- ✅ Seed script (JSON → Medusa)
- ⏳ Deploy en Railway (pendiente)
- ⏳ Deploy en Vercel (pendiente)
- ⏳ MercadoPago (pendiente)
