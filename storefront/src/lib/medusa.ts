const MEDUSA_BACKEND_URL =
  process.env.NEXT_PUBLIC_MEDUSA_BACKEND_URL || "http://localhost:9000"
const MEDUSA_PUBLISHABLE_KEY =
  process.env.NEXT_PUBLIC_MEDUSA_PUBLISHABLE_KEY || ""
const ARGENTINA_REGION_ID = process.env.MEDUSA_ARGENTINA_REGION_ID || ""

const FIELDS =
  "id,title,handle,description,metadata,thumbnail,*images,*categories,*variants"

export interface Product {
  sku: string
  name: string
  description: string
  category: string
  prices: {
    precio_lista: number | null
    precio_efectivo: number | null
    precio_transferencia: number | null
    precio_mayorista: number | null
    cuotas: number | null
    cuota_valor: number | null
  }
  images: string[]
  slug: string
}

export interface Category {
  id: string
  name: string
  slug: string
  count: number
}

interface MedusaVariant {
  sku?: string
  calculated_price?: { calculated_amount?: number }
}

interface MedusaProduct {
  id: string
  title: string
  handle: string
  description?: string
  thumbnail?: string
  metadata?: Record<string, unknown>
  images?: { url: string }[]
  categories?: { name: string }[]
  variants?: MedusaVariant[]
}

function num(v: unknown): number | null {
  if (typeof v === "number" && !Number.isNaN(v)) return v
  return null
}

export function mapProduct(p: MedusaProduct): Product {
  const m = (p.metadata || {}) as Record<string, unknown>
  const firstVariant = p.variants?.[0]
  return {
    sku: firstVariant?.sku || p.handle,
    name: p.title,
    description: p.description || "",
    category: p.categories?.[0]?.name || "General",
    prices: {
      precio_lista: num(m.precio_lista),
      precio_efectivo: num(m.precio_efectivo),
      precio_transferencia: num(m.precio_transferencia),
      precio_mayorista: num(m.precio_mayorista),
      cuotas: num(m.cuotas),
      cuota_valor: num(m.cuota_valor),
    },
    images: (p.images?.map((i) => i.url) || []).filter(Boolean),
    slug: p.handle,
  }
}

function storeUrl(path: string, params: Record<string, string>): string {
  const sp = new URLSearchParams(params)
  if (ARGENTINA_REGION_ID) sp.set("region_id", ARGENTINA_REGION_ID)
  return `${MEDUSA_BACKEND_URL}${path}?${sp}`
}

async function storeFetch(url: string) {
  const res = await fetch(url, {
    cache: "no-store",
    headers: MEDUSA_PUBLISHABLE_KEY
      ? { "x-publishable-api-key": MEDUSA_PUBLISHABLE_KEY }
      : {},
  })
  if (!res.ok) throw new Error(`Medusa store error ${res.status}`)
  return res.json()
}

export async function getProducts(params?: {
  limit?: number | string
  offset?: number | string
  category_id?: string
  q?: string
  handle?: string
}): Promise<{ products: Product[]; total: number }> {
  const qp: Record<string, string> = { fields: FIELDS, limit: "100" }
  if (params?.limit) qp.limit = String(params.limit)
  if (params?.offset) qp.offset = String(params.offset)
  if (params?.category_id) qp.category_id = params.category_id
  if (params?.q) qp.q = params.q
  if (params?.handle) qp.handle = params.handle

  const data = await storeFetch(storeUrl("/store/products", qp))
  return {
    products: (data.products || []).map(mapProduct),
    total: data.count || 0,
  }
}

export async function getProduct(handle: string): Promise<Product | null> {
  const { products } = await getProducts({ handle, limit: "1" })
  return products[0] || null
}

export async function getCategories(): Promise<Category[]> {
  const [catData, { products }] = await Promise.all([
    storeFetch(storeUrl("/store/product-categories", { fields: "id,name,handle" })),
    getProducts({ limit: "1000" }),
  ])

  const cats = (catData.product_categories || []) as {
    id: string
    name: string
    handle: string
  }[]

  const countByCat: Record<string, number> = {}
  for (const p of products) {
    const c = p.category
    countByCat[c] = (countByCat[c] || 0) + 1
  }

  return cats.map((c) => ({ id: c.id, name: c.name, slug: c.handle || c.id, count: countByCat[c.name] || 0 }))
}
