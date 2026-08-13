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

- **Producción (Railway/Vercel):**
  ```
  pk_fc06e44a06bc2556affab5c23313b32a8bf5213371a09a482c9479f3ec82fc17
  ```
- **Local (base de datos Docker):**
  ```
  pk_8eee05fa38bf73afe6aa4e6cb494c0a57b01e30aed7533dec018f7fef1e6dcd9
  ```

> ⚠️ La clave de producción NO sirve contra la instancia local y viceversa.
> Al buildear el storefront local hay que usar la clave **local** (ver más abajo).

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
| `GITHUB_TOKEN` | `github_pat_...` (configurado, permisos Contents: Read and Write) |
| `MERCADOPAGO_ACCESS_TOKEN` | _(pendiente — token de acceso de MercadoPago, producción o TEST)_ |
| `MERCADOPAGO_PUBLIC_KEY` | _(pendiente — clave pública de MercadoPago)_ |
| `NEXT_PUBLIC_BASE_URL` | `https://dankoshop.vercel.app` (para los back_urls de pago) |
| `NEXT_PUBLIC_ENVIO_FEE` | costo de envío por debajo de $50.000 (opcional) |
| `NEXT_PUBLIC_BANCO_TITULAR` | titular de la cuenta (ej. `DANKOSHOP S.R.L.`) |
| `NEXT_PUBLIC_BANCO_CBU` | CBU de DankoShop |
| `NEXT_PUBLIC_BANCO_ALIAS` | alias CVU (ej. `danko.shop.cbu`) |
| `NEXT_PUBLIC_BANCO_CUIT` | CUIT de DankoShop |
| `NEXT_PUBLIC_BANCO_NOMBRE` | nombre del banco |

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
  python3 scripts/sync_excel_to_medusa.py
```

### Sync local (para pruebas)

```bash
MEDUSA_BACKEND_URL=http://localhost:9100 python3 scripts/sync_excel_to_medusa_local.py
```

### Frontend local

```bash
cd storefront
NEXT_PUBLIC_MEDUSA_BACKEND_URL=http://localhost:9100 \
  NEXT_PUBLIC_MEDUSA_PUBLISHABLE_KEY=pk_8eee05fa38bf73afe6aa4e6cb494c0a57b01e30aed7533dec018f7fef1e6dcd9 \
  npm run dev
```

> La clave publicable local es la de la base Docker, NO la de producción.

### Backend local (control de instancias)

```bash
./scripts/medusa-local.sh status   # estado de contenedores + Medusa
./scripts/medusa-local.sh start    # levanta UNA instancia (si no hay otra)
./scripts/medusa-local.sh stop     # detiene la instancia (aunque esté colgada)
./scripts/medusa-local.sh restart  # stop + start
```

### Railway deploy

```bash
railway login
railway link
railway up
```

## Gestión Local (evita cuelgues y sobrecalentamiento)

El entorno local depende de 2 contenedores Docker + 1 instancia de Medusa en `:9100`.
Para que no se cuelguen instancias ni se queme la notebook:

1. **Los contenedores se auto-reinician** (`restart: unless-stopped`):
   ```bash
   docker update --restart unless-stopped dankoshop-postgres dankoshop-redis
   ```
   Con esto, si Docker se reinicia (o la notebook se apaga/duerme), los contenedores
   vuelven a levantarse solos al arrancar el sistema.

2. **Siempre usar el script** `scripts/medusa-local.sh` para arrancar Medusa.
   El script:
   - Arranca los contenedores si están caídos y espera a que PostgreSQL responda.
   - **Rechaza levantar una 2ª instancia** si el puerto `:9100` ya está ocupado.
   - `stop` mata la instancia aunque sea un proceso huérfano/colgado (sin terminal).
   - Guarda el PID en `/tmp/medusa-local.pid` y el log en `/tmp/medusa-local.log`.

> ⚠️ **NO** levantar Medusa a mano en varias terminales. Eso es lo que causó el
> incidente del 06/08: 4 instancias corriendo, una colgada al 91.8% de CPU
> (sobrecalentamiento + 6.8 GB de RAM) porque PostgreSQL estaba detenido.

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
│   ├── sync_excel_to_medusa.py → Excel → Medusa producción
│   ├── sync_excel_to_medusa_local.py → Excel → Medusa local
│   ├── sync_medusa_to_excel.py → Medusa producción → Excel
│   ├── sync_medusa_to_excel_local.py → Medusa local → Excel
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

## Checkout y Pagos (online)

Flujo implementado en el storefront (Next.js), sin depender del módulo de pagos de Medusa:

- **`/checkout`** — formulario de datos + envío + selector de método de pago.
  - **Mercado Pago** (tarjeta crédito/débito, dinero en cuenta, efectivo/Rapipago/Pago Fácil):
    crea una preferencia en `POST /api/mercadopago/preference` (usa `MERCADOPAGO_ACCESS_TOKEN`)
    y redirige al checkout seguro de Mercado Pago.
  - **Transferencia bancaria** (Alias CVU): muestra los datos de la cuenta (CBU/alias) y genera
    el comprobante pendiente; se confirma manualmente al acreditarse.
- **`/comprobante`** — recibo imprimible / PDF del pedido con todos los datos, y las
  instrucciones de transferencia si corresponde.
- **`POST /api/ordenes`** — registra pedidos en `data/pedidos.json` vía GitHub (usa `GITHUB_TOKEN`).
- **`POST /api/mercadopago/notification`** — webhook de Mercado Pago que marca el pedido como "pagado"
  cuando `payment.approved`.

> **Para activar el pago online real** hace falta cargar en Vercel:
> `MERCADOPAGO_ACCESS_TOKEN` (y `MERCADOPAGO_PUBLIC_KEY`) + los datos del banco
> (`NEXT_PUBLIC_BANCO_CBU`, `NEXT_PUBLIC_BANCO_ALIAS`, etc.). Sin el token, el botón de
> Mercado Pago devuelve un error claro; la transferencia bancaria funciona siempre.

### Configuración rápida de los datos bancarios (env vars Vercel)

```
NEXT_PUBLIC_BANCO_TITULAR=DANKOSHOP S.R.L.
NEXT_PUBLIC_BANCO_CBU=000000310000...
NEXT_PUBLIC_BANCO_ALIAS=mi.alias.cvu
NEXT_PUBLIC_BANCO_CUIT=30-12345678-9
NEXT_PUBLIC_BANCO_NOMBRE=Mi Banco
```

## Solución de Problemas

### El sitio no muestra productos
1. Verificar que las env vars de Vercel estén configuradas
2. Verificar que Railway esté online: `railway status`
3. Probar la API: `curl https://dankoshop-api-production.up.railway.app/health`

### Los precios no se muestran
1. Verificar que el seed corrió en Railway (ver logs)
2. Correr el sync: `python3 scripts/sync_excel_to_medusa.py`

### El editor no guarda cambios
1. Verificar que `GITHUB_TOKEN` esté configurado en Vercel
2. Verificar que el token tenga permisos de escritura en el repo

### Build de Vercel falla
1. Verificar que no hay errores de TypeScript: `cd storefront && npx tsc --noEmit`
2. Verificar el build local: `cd storefront && npm run build`

### La notebook calienta / Medusa "cuelga" (local)
1. Revisar si hay instancias duplicadas: `./scripts/medusa-local.sh status`
2. Verificar que los contenedores estén arriba: `docker ps`
3. Si el storefront local da 500 con clave inválida, rebuildear con la clave local:
   ```bash
   cd storefront
   NEXT_PUBLIC_MEDUSA_BACKEND_URL=http://localhost:9100 \
     NEXT_PUBLIC_MEDUSA_PUBLISHABLE_KEY=pk_8eee05fa38bf73afe6aa4e6cb494c0a57b01e30aed7533dec018f7fef1e6dcd9 \
     npm run build && ./node_modules/.bin/next start -p 3005
   ```
4. Si hay procesos Medusa colgados (más de una instancia, CPU alta):
   `./scripts/medusa-local.sh stop` y luego `./scripts/medusa-local.sh start`
