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
│   │   ├── categoria/   → Productos por categoría
│   │   └── producto/    → Detalle de producto con galería
│   ├── src/components/  → header, footer, product-image (zoom/modal)
│   └── src/data/        → products.ts (114 productos hardcodeados con URLs Cloudinary)
├── medusa-backend/      → MedusaJS v2 (admin de productos, pedidos, pagos)
│   └── apps/backend/    → Backend principal
├── scripts/             → Scripts Python (sync, seed, parse_chat, upload_cloudinary)
├── data/                → products.json, products.csv, image_urls.json, organized_images/
└── excel/               → Excel maestro de productos
```

## Tech Stack
- **Frontend:** Next.js 16, React 19, Tailwind CSS 4, lucide-react
- **Backend:** MedusaJS v2.18, Node.js 22, PostgreSQL 16, Redis 7
- **Imágenes:** Cloudinary (cloud_name: xjuisove)
- **Hosting frontend:** Vercel (https://dankoshop.vercel.app)
- **Hosting backend:** Railway (pendiente)
- **DB:** Docker (dankoshop-postgres, dankoshop-redis en network dankoshop-net)
- **Package manager:** pnpm (monorepo con pnpm-workspace.yaml)

## Docker Containers
- `dankoshop-postgres` → localhost:5432, user: dankoshop, pass: dankoshop, db: dankoshop
- `dankoshop-redis` → localhost:6379

## Medusa Backend
- Puerto: 9000
- Admin URL: http://localhost:9000/app
- Admin credentials: admin@dankoshop.com / supersecret
- Auth API: POST /auth/user/emailpass (Medusa v2, NO /admin/auth)
- DB migrate: `pnpm exec medusa db:migrate`
- Seed: `python3 scripts/seed.py`
- Arrancar: `pnpm exec medusa develop`

## Commands útiles
```bash
# Frontend
cd storefront && npm run build    # Build local (usar Node 20)
nvm use 20 && cd storefront && npm run dev

# Backend
nvm use 22 && cd medusa-backend && pnpm exec medusa develop

# Docker
docker ps                         # Ver containers
docker exec dankoshop-postgres psql -U dankoshop -dankoshop -c "SELECT 1;"

# Upload imágenes a Cloudinary
python3 scripts/upload_cloudinary.py

# Seed productos a Medusa
python3 scripts/seed.py

# Generar Excel
python3 scripts/create_excel.py
```

## Variables de entorno
Medusa backend (.env):
```
DATABASE_URL=postgresql://dankoshop:dankoshop@localhost:5432/dankoshop
REDIS_URL=redis://localhost:6379
JWT_SECRET=super-secret-jwt-change-in-production
COOKIE_SECRET=super-secret-cookie-change-in-production
```

## GitHub
- Repo: https://github.com/dankopetro/dankoshop
- Branch: main
- GitHub Actions workflow: .github/workflows/deploy.yml (secrets no configurados)

## Lo que está hecho
1. ✅ Parser de chat de WhatsApp (scripts/parse_chat.py)
2. ✅ 114 productos parseados con precios e imágenes
3. ✅ Excel con productos (data/productos_dankoshop.xlsx)
4. ✅ Frontend Next.js desplegado en Vercel
5. ✅ 704 imágenes subidas a Cloudinary
6. ✅ Páginas: home, productos, categorías, detalle con zoom
7. ✅ Medusa backend funcionando local con 113 productos
8. ✅ Docker PostgreSQL + Redis corriendo

## Lo que falta
1. ❌ Deployar Medusa backend en Railway
2. ❌ Conectar frontend Vercel con backend Railway (productos dinámicos)
3. ❌ Configurar MercadoPago (pagos)
4. ❌ Dominio propio (cuando esté listo)
5. ❌ Variables de entorno de Vercel (NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME etc.)
6. ❌ GitHub secrets para CI/CD

## Notas importantes
- El frontend muestra productos HARD CODEADOS en products.ts, NO se conecta al backend todavía
- Las imágenes son de Cloudinary, NO están en el repo
- Medusa v2 usa auth diferente: /auth/user/emailpass (no /admin/auth)
- package.json del backend tiene "packageManager": "pnpm@9.15.9"
- pnpm funciona con Node 22, npm necesita mirror registry (registry.npmmirror.com)
- El .npmrc en la raíz del repo configura el mirror para evitar 429 de npm
