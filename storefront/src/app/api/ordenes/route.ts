import { NextRequest, NextResponse } from "next/server"
import { Order } from "@/lib/checkout"
import { formatOrderMessage, sendTelegram } from "@/lib/telegram"

const GITHUB_TOKEN = process.env.GITHUB_TOKEN
const GITHUB_REPO = process.env.GITHUB_REPO || "dankopetro/dankoshop"
const GITHUB_BRANCH = process.env.GITHUB_BRANCH || "main"
const ORDERS_PATH = "data/pedidos.json"

async function getCurrentFile() {
  const res = await fetch(
    `https://api.github.com/repos/${GITHUB_REPO}/contents/${ORDERS_PATH}?ref=${GITHUB_BRANCH}`,
    { headers: { Authorization: `Bearer ${GITHUB_TOKEN}` } },
  )
  if (res.status === 404) return null
  const body = await res.json().catch(() => ({}))
  if (!body.sha) return null
  const content = Buffer.from(body.content, "base64").toString("utf-8")
  return { sha: body.sha as string, data: JSON.parse(content || "[]") }
}

export async function GET() {
  if (!GITHUB_TOKEN) return NextResponse.json({ error: "GITHUB_TOKEN no configurado" }, { status: 500 })
  const file = await getCurrentFile()
  return NextResponse.json(file?.data || [])
}

export async function POST(req: NextRequest) {
  if (!GITHUB_TOKEN) {
    return NextResponse.json({ error: "GITHUB_TOKEN no configurado" }, { status: 500 })
  }
  const body = await req.json().catch(() => null)
  if (!body || !body.order || !Array.isArray(body.order.items)) {
    return NextResponse.json({ error: "Pedido inválido" }, { status: 400 })
  }

  try {
    const current = await getCurrentFile()
    const orders = Array.isArray(current?.data) ? current.data : []
    const idx = orders.findIndex((o: any) => o.id === body.order.id)
    if (idx >= 0) orders[idx] = body.order
    else orders.push(body.order)

    const content = JSON.stringify(orders, null, 2) + "\n"
    const url = `https://api.github.com/repos/${GITHUB_REPO}/contents/${ORDERS_PATH}`
    const put = await fetch(url, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${GITHUB_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: `Registrar pedido ${body.order.id}`,
        content: Buffer.from(content).toString("base64"),
        sha: current?.sha,
        branch: GITHUB_BRANCH,
      }),
    })

    if (!put.ok) {
      const err = await put.text()
      return NextResponse.json({ error: `Error al guardar pedido: ${err}` }, { status: 500 })
    }

    const saved = orders.find((o: any) => o.id === body.order.id)
    if (saved) {
      await sendTelegram(formatOrderMessage(saved as Order, "nuevo"))
    }

    return NextResponse.json({ ok: true })
  } catch (e) {
    return NextResponse.json(
      { error: `Error: ${e instanceof Error ? e.message : String(e)}` },
      { status: 500 },
    )
  }
}
