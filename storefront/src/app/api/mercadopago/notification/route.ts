import { NextRequest, NextResponse } from "next/server"
import { Order } from "@/lib/checkout"
import { formatOrderMessage, sendTelegram } from "@/lib/telegram"

const GITHUB_REPO = process.env.GITHUB_REPO || "dankopetro/dankoshop"
const GITHUB_BRANCH = process.env.GITHUB_BRANCH || "main"
const ORDERS_PATH = "data/pedidos.json"

async function getCurrentFile() {
  const res = await fetch(
    `https://api.github.com/repos/${GITHUB_REPO}/contents/${ORDERS_PATH}?ref=${GITHUB_BRANCH}`,
    { headers: { Authorization: `Bearer ${process.env.GITHUB_TOKEN}` } },
  )
  if (res.status === 404) return null
  const body = await res.json().catch(() => ({}))
  if (!body.sha) return null
  return { sha: body.sha as string, data: JSON.parse(Buffer.from(body.content, "base64").toString()) }
}

async function getMercadoPagoPayment(paymentId: string) {
  const token = process.env.MERCADOPAGO_ACCESS_TOKEN
  const res = await fetch(`https://api.mercadopago.com/v1/payments/${paymentId}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) return null
  return res.json().catch(() => null)
}

export async function POST(req: NextRequest) {
  const token = process.env.MERCADOPAGO_ACCESS_TOKEN
  if (!token) return NextResponse.json({ error: "No configurado" }, { status: 500 })

  const type = req.nextUrl.searchParams.get("type") || req.nextUrl.searchParams.get("topic")
  const body = await req.json().catch(() => ({}))
  const data = body.data || (Array.isArray(body) ? body[0]?.data : null)
  const paymentId = data?.id
  if (!paymentId) return NextResponse.json({ ok: true })

  if (type === "payment" || type === "mercadopago") {
    const payment = await getMercadoPagoPayment(paymentId)
    if (payment) {
      const ref = payment.external_reference
      if (ref && payment.status === "approved") {
        try {
          const current = await getCurrentFile()
          const orders = Array.isArray(current?.data) ? current.data : []
          const idx = orders.findIndex((o: any) => o.id === ref || o.id === String(ref))
          if (idx >= 0) {
            orders[idx].estado = "pagado"
            orders[idx].pago_ref = String(paymentId)
            orders[idx].metodo_pago_label = payment.payment_method_id || "mercadopago"
            const content = JSON.stringify(orders, null, 2) + "\n"
            const put = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/contents/${ORDERS_PATH}`, {
              method: "PUT",
              headers: {
                Authorization: `Bearer ${process.env.GITHUB_TOKEN}`,
                "Content-Type": "application/json",
              },
              body: JSON.stringify({
                message: `Pago aprobado: ${ref} (${paymentId})`,
                content: Buffer.from(content).toString("base64"),
                sha: current?.sha,
                branch: GITHUB_BRANCH,
              }),
            })
            if (put.ok) {
              await sendTelegram(formatOrderMessage(orders[idx] as Order, "pagado"))
            }
          }
        } catch {
          // no hacer fallar el webhook
        }
      }
    }
  }

  return NextResponse.json({ ok: true })
}
