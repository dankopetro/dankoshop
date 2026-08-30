import { NextRequest, NextResponse } from "next/server"

const MEDUSA_URL = process.env.NEXT_PUBLIC_MEDUSA_BACKEND_URL || "http://localhost:9000"
const ADMIN_EMAIL = process.env.MEDUSA_ADMIN_EMAIL || "admin@dankoshop.com"
const ADMIN_PASSWORD = process.env.MEDUSA_ADMIN_PASSWORD || ""

async function getAdminToken(): Promise<string | null> {
  if (!ADMIN_PASSWORD) return null
  try {
    const res = await fetch(`${MEDUSA_URL}/auth/user/emailpass`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: ADMIN_EMAIL, password: ADMIN_PASSWORD }),
    })
    if (!res.ok) return null
    const data = await res.json()
    return data.token || null
  } catch {
    return null
  }
}

export async function POST(req: NextRequest) {
  try {
    const { skus } = await req.json()
    if (!Array.isArray(skus) || skus.length === 0) {
      return NextResponse.json({ error: "skus array required" }, { status: 400 })
    }

    const token = await getAdminToken()
    if (!token) {
      return NextResponse.json({ error: "Auth failed" }, { status: 500 })
    }

    const headers = { Authorization: `Bearer ${token}` }
    const stock: Record<string, number | null> = {}

    // Fetch all inventory items (max 100 per page)
    let offset = 0
    const invMap: Record<string, number> = {}
    while (true) {
      const res = await fetch(`${MEDUSA_URL}/admin/inventory-items?limit=100&offset=${offset}`, { headers })
      if (!res.ok) break
      const data = await res.json()
      for (const item of data.inventory_items || []) {
        const sku = item.sku
        if (!sku) continue
        const total = (item.location_levels || []).reduce(
          (sum: number, l: any) => sum + (l.stocked_quantity || 0), 0
        )
        invMap[sku] = total
      }
      if ((data.inventory_items || []).length < 100) break
      offset += 100
    }

    // Map requested SKUs to stock
    for (const sku of skus) {
      stock[sku] = sku in invMap ? invMap[sku] : null
    }

    return NextResponse.json({ stock })
  } catch {
    return NextResponse.json({ error: "Internal error" }, { status: 500 })
  }
}
