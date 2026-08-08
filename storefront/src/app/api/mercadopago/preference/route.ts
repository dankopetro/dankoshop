import { NextRequest, NextResponse } from "next/server"

interface MPItem {
  sku: string
  name: string
  price: number
  quantity: number
}

export async function POST(req: NextRequest) {
  const token = process.env.MERCADOPAGO_ACCESS_TOKEN
  if (!token) {
    return NextResponse.json(
      { error: "MERCADOPAGO_ACCESS_TOKEN no está configurado en el servidor." },
      { status: 500 },
    )
  }

  const body = await req.json().catch(() => null)
  if (!body || !Array.isArray(body.items) || body.items.length === 0) {
    return NextResponse.json({ error: "Sin items para generar la preferencia" }, { status: 400 })
  }

  const base =
    process.env.NEXT_PUBLIC_BASE_URL ||
    (process.env.NODE_ENV === "production"
      ? "https://dankoshop.com.ar"
      : "http://localhost:3005")

  const items = (body.items as MPItem[]).map((it) => ({
    id: String(it.sku),
    title: String(it.name).slice(0, 240),
    quantity: Number(it.quantity) || 1,
    unit_price: Math.round(Number(it.price) || 0),
    currency_id: "ARS",
  }))

  const externalRef = String(body.external_reference || `DK-${Date.now()}`)

  const preference = {
    items,
    external_reference: externalRef,
    statement_descriptor: "DANKOSHOP",
    payment_methods: {
      installments: 12,
      default_installments: 1,
    },
    back_urls: {
      success: `${base}/comprobante?status=success&ref=${externalRef}`,
      pending: `${base}/comprobante?status=pending&ref=${externalRef}`,
      failure: `${base}/comprobante?status=failure&ref=${externalRef}`,
    },
    auto_return: "approved",
    notification_url: `${base}/api/mercadopago/notification`,
  }

  try {
    const res = await fetch("https://api.mercadopago.com/checkout/preferences", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(preference),
    })

    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      return NextResponse.json(
        { error: data.message || `MercadoPago respondió ${res.status}` },
        { status: 500 },
      )
    }

    return NextResponse.json({
      init_point: data.init_point,
      sandbox_init_point: data.sandbox_init_point,
      preference_id: data.id,
      external_reference: externalRef,
    })
  } catch (e) {
    return NextResponse.json(
      { error: `Error: ${e instanceof Error ? e.message : String(e)}` },
      { status: 500 },
    )
  }
}
