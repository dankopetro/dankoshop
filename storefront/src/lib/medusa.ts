const MEDUSA_BACKEND_URL = process.env.NEXT_PUBLIC_MEDUSA_BACKEND_URL || "http://localhost:9000"

export async function getProducts(params?: { limit?: number; offset?: number; category?: string; q?: string }) {
  const searchParams = new URLSearchParams()
  if (params?.limit) searchParams.set("limit", String(params.limit))
  if (params?.offset) searchParams.set("offset", String(params.offset))
  if (params?.q) searchParams.set("q", params.q)
  
  const res = await fetch(`${MEDUSA_BACKEND_URL}/store/products?${searchParams}`, { cache: "no-store" })
  if (!res.ok) throw new Error("Failed to fetch products")
  return res.json()
}

export async function getProduct(handle: string) {
  const res = await fetch(`${MEDUSA_BACKEND_URL}/store/products?handle=${handle}`, { cache: "no-store" })
  if (!res.ok) throw new Error("Failed to fetch product")
  const data = await res.json()
  return data.products?.[0] || null
}

export async function getCategories() {
  const res = await fetch(`${MEDUSA_BACKEND_URL}/store/product-categories?limit=100`, { cache: "no-store" })
  if (!res.ok) return []
  const data = await res.json()
  return data.product_categories || []
}

export async function getProductById(id: string) {
  const res = await fetch(`${MEDUSA_BACKEND_URL}/store/products/${id}`, { cache: "no-store" })
  if (!res.ok) throw new Error("Failed to fetch product")
  return res.json()
}