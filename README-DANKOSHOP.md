# DankoShop - Guía Completa del Proyecto

## URLs y Links

| Servicio | URL |
|----------|-----|
| **Tienda online** | https://dankoshop.vercel.app |
| **Backend API** | https://dankoshop-api-production.up.railway.app |
| **Admin Panel** | https://dankoshop-api-production.up.railway.app/app |
| **Editor de contenido** | https://dankoshop.vercel.app/admin-contenido |
| **GitHub** | https://github.com/dankopetro/dankoshop |
| **Railway** | https://railway.com/project/43f44001-29b4-4bf8-ac5b-faceff49a9dc |
| **Vercel** | https://vercel.com/dankopetros-projects |

## Credenciales

| Servicio | Usuario / Email | Contraseña / Token |
|----------|----------------|-------------------|
| **Admin Medusa** | admin@dankoshop.com | supersecret |
| **Editor contenido** | (sin usuario) | danko-admin-2026 |
| **GitHub** | dankopetro | (tu contraseña) |
| **Cloudinary** | cloud_name: xjuisove | api_key: 645939449555487 |

## Publishable API Key (para la API store)

```
pk_fc06e44a06bc2556affab5c23313b32a8bf5213371a09a482c9479f3ec82fc17
```

## Datos del Negocio

- **Dirección:** Calle 26 Número 207, La Plata, Buenos Aires
- **WhatsApp / Teléfono:** 221 621 9596
- **Horarios:** Lunes a Sábados de 9:00 a 19:00 hs
- **Envío gratis:** en compras superiores a $50.000

## Variables de Entorno

### Vercel (Storefront)

| Variable | Valor |
|----------|-------|
| `NEXT_PUBLIC_MEDUSA_BACKEND_URL` | `https://dankoshop-api-production.up.railway.app` |
| `NEXT_PUBLIC_MEDUSA_PUBLISHABLE_KEY` | `pk_fc06e44a06bc2556affab5c23313b32a8bf5213371a09a482c9479f3ec82fc17` |
| `CONTENT_ADMIN_PASSWORD` | `danko-admin-2026` |
| `GITHUB_TOKEN` | _(pendiente de configurar)_ |

### Railway (Backend)

Las variables de Railway se generan automáticamente. Las principales son:
- `DATABASE_URL` — PostgreSQL (generado por Railway)
- `REDIS_URL` — Redis (generado por Railway)
- `STORE_CORS` — https://dankoshop.vercel.app,http://localhost:3000
- `ADMIN_CORS` — http://localhost:9000,http://localhost:7001
- `AUTH_CORS` — https://dankoshop.vercel.app,http://localhost:3000,http://localhost:9000

## Comandos Útiles

### Conectar a la tienda online

```bash
# Ver productos desde la API store
curl -s "https://dankoshop-api-production.up.railway.app/store/products?limit=3&region_id=REGION_ID&fields=id,title,handle,metadata,*variants" \
  -H "x-publishable-api-key: pk_fc06e44a06bc2556affab5c23313b32a8bf5213371a09a482c9479f3ec82fc17"

# Login admin Medusa
curl -X POST "https://dankoshop-api-production.up.railway.app/auth/user/emailpass" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@dankoshop.com","password":"supersecret"}'
```

### Sync Excel → Medusa v2 (producción)

```bash
MEDUSA_BACKEND_URL=https://dankoshop-api-production.up.railway.app \
  MEDUSA_ADMIN_EMAIL=admin@dankoshop.com \
  MEDUSA_ADMIN_PASSWORD=supersecret \
  python3 scripts/sync_excel.py
```

### Sync local (para pruebas)

```bash
MEDUSA_BACKEND_URL=http://localhost:9000 python3 scripts/sync_excel.py
```

### Frontend local

```bash
cd storefront
NEXT_PUBLIC_MEDUSA_BACKEND_URL=http://localhost:9000 \
  NEXT_PUBLIC_MEDUSA_PUBLISHABLE_KEY=pk_fc06e44a06bc2556affab5c23313b32a8bf5213371a09a482c9479f3ec82fc17 \
  npm run dev
```

### Backend local

```bash
cd medusa-backend
DATABASE_URL=postgresql://dankoshop:dankoshop@localhost:5432/dankoshop \
  REDIS_URL=redis://localhost:6379 \
  pnpm exec medusa develop
```

### Railway deploy

```bash
railway login
railway link
railway up
```

## Precios

La web pública muestra **solo precios minoristas**:
- **Precio efectivo** — precio con descuento por pago en efectivo
- **Precio transferencia** — precio por transferencia bancaria
- **Cuotas** — cantidad y valor de cuotas sin interés
- **Precio lista** — precio de referencia (tachado)

Los precios **mayoristas** son internos (no se muestran en la web).

### Archivos de precios

- `excel/Productos_Maestro.xlsx` — Excel maestro con todos los precios (114 productos)
- `data/products.json` — JSON generado desde el Excel
- `data/image_urls.json` — URLs de Cloudinary por SKU

## Arquitectura del Proyecto

```
dankoshop/
├── storefront/              → Next.js 16 (frontend)
│   ├── src/app/             → Páginas (App Router)
│   │   ├── page.tsx         → Home
│   │   ├── productos/       → Catálogo
│   │   ├── categorias/      → Listado categorías
│   │   ├── categoria/       → Productos por categoría
│   │   ├── producto/        → Detalle producto
│   │   ├── admin-contenido/ → Editor de contenido
│   │   ├── contacto/        → Contacto
│   │   ├── nosotros/        → Sobre nosotros
│   │   ├── envios/          → Envíos y devoluciones
│   │   ├── faq/             → Preguntas frecuentes
│   │   ├── pagos/           → Métodos de pago
│   │   ├── terminos/        → Términos y condiciones
│   │   ├── privacidad/      → Política de privacidad
│   │   ├── carrito/         → Carrito (checkout por WhatsApp)
│   │   └── api/contenido/   → API para guardar contenido
│   ├── src/content/         → JSON editables (nosotros, envios, etc.)
│   └── src/lib/medusa.ts    → Cliente Medusa Store API
├── medusa-backend/          → MedusaJS v2.18
│   └── apps/backend/
│       ├── seed-products.cjs → Seed upsert de productos
│       └── src/              → Código fuente del backend
├── scripts/
│   ├── sync_excel.py        → Sync Excel → Medusa v2 (REST API)
│   ├── seed.py              → Seed local
│   └── vercel-env.sh        → Configurar env vars de Vercel
├── excel/
│   └── Productos_Maestro.xlsx → Maestro de productos
├── data/
│   ├── products.json        → Productos en JSON
│   ├── image_urls.json      → URLs de Cloudinary
│   └── organized_images/    → Imágenes organizadas por SKU
├── Dockerfile               → Build para Railway
└── railway.toml             → Config Railway
```

## Datos Técnicos

- **Frontend:** Next.js 16, React 19, Tailwind CSS 4
- **Backend:** MedusaJS v2.18, Node.js 22, PostgreSQL 16, Redis 7
- **Imágenes:** Cloudinary (cloud: xjuisove)
- **Hosting:** Vercel (frontend) + Railway (backend)
- **Base de datos:** PostgreSQL 16 (Railway)
- **Región ARS:** reg_01KZCDHFKD3X8KMZ45NPV8HKZF
- **Productos:** 114 (sin contar los 4 demos de Medusa)
- **Categorías:** 16 activas

## Editor de Contenido

El editor está en https://dankoshop.vercel.app/admin-contenido

Para usarlo:
1. Ingresá la contraseña: `danko-admin-2026`
2. Seleccioná la página a editar
3. Modificá el JSON (cambiá los textos entre comillas)
4. Hacé click en "Guardar cambios"

Los cambios se publican automáticamente al repo GitHub y Vercel redespliega.

**Nota:** Para que funcione el guardado, necesitás configurar la env var `GITHUB_TOKEN` en Vercel con un token de GitHub con permisos de escritura en el repo.

## Solución de Problemas

### El sitio no muestra productos
1. Verificar que las env vars de Vercel estén configuradas
2. Verificar que Railway esté online: `railway status`
3. Probar la API: `curl https://dankoshop-api-production.up.railway.app/health`

### Los precios no se muestran
1. Verificar que el seed corrió en Railway (ver logs)
2. Correr el sync: `MEDUSA_BACKEND_URL=https://dankoshop-api-production.up.railway.app python3 scripts/sync_excel.py`

### El editor no guarda cambios
1. Verificar que `GITHUB_TOKEN` esté configurado en Vercel
2. Verificar que el token tenga permisos de escritura en el repo

### Build de Vercel falla
1. Verificar que no hay errores de TypeScript: `cd storefront && npx tsc --noEmit`
2. Verificar el build local: `cd storefront && npm run build`
