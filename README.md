# DankoShop 🛒

E-commerce headless: **Next.js 14 (Storefront) + MedusaJS v2 (Backend)**

## Stack
- **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: MedusaJS v2 + PostgreSQL + Redis
- **Payments**: MercadoPago (Argentina) + Stripe (opcional)
- **Hosting**: Vercel (storefront) + Railway (backend + DB)
- **Sync**: Excel (LibreOffice) → Medusa via script Python

## Estructura
```
dankoshop/
├── medusa-backend/     # API Medusa + Admin
├── storefront/         # Next.js Storefront
├── scripts/            # sync_excel_to_medusa.py, seed.js
├── data/               # products.json, products.csv (generados)
├── excel/              # Productos_Maestro.xlsx (local only, .gitignored)
├── package.json        # Workspaces root
└── turbo.json          # Turborepo config
```

## Comandos
```bash
# Instalar todo
npm install

# Desarrollo (terminales separadas)
npm run dev:backend   # Medusa en :9000
npm run dev:store     # Next.js en :3000

# Sincronizar Excel → Medusa
npm run sync:excel

# Build producción
npm run build

# Seed inicial (solo primera vez)
npm run seed
```

## Variables de Entorno
Copia `.env.example` a cada `.env` y completa:
- `medusa-backend/.env` → DB, JWT, MercadoPago, CORS
- `storefront/.env.local` → BACKEND_URL

## Deploy
- **Vercel**: Conecta repo → Root: `storefront` → Env Vars → Deploy
- **Railway**: New Project → GitHub → `medusa-backend` → Add PostgreSQL + Redis → Deploy

## Flujo Diario
1. Edita `excel/Productos_Maestro.xlsx` en LibreOffice
2. `npm run sync:excel` → actualiza Medusa
3. `git add -A && git commit -m "update products" && git push`
4. Vercel + Railway auto-deployan

## Licencia
MIT