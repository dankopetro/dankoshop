import { Order } from "./checkout"

const BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN
const CHAT_ID = process.env.TELEGRAM_CHAT_ID

export function telegramConfigured(): boolean {
  return Boolean(BOT_TOKEN && CHAT_ID)
}

export async function sendTelegram(text: string): Promise<boolean> {
  if (!BOT_TOKEN || !CHAT_ID) return false
  try {
    const res = await fetch(`https://api.telegram.org/bot${BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chat_id: CHAT_ID,
        text,
        parse_mode: "HTML",
        disable_web_page_preview: true,
      }),
    })
    return res.ok
  } catch {
    return false
  }
}

const METODO_PAGO_LABEL: Record<string, string> = {
  mercadopago: "Mercado Pago",
  transferencia: "Transferencia",
}

const ESTADO_LABEL: Record<string, string> = {
  pendiente: "⏳ Pendiente",
  pagado: "✅ Pagado",
  fallido: "❌ Fallido",
}

function esc(s: string | null | undefined): string {
  if (!s) return ""
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
}

function fmtARS(n: number): string {
  return "$" + Math.round(n).toLocaleString("es-AR")
}

export function formatOrderMessage(order: Order, tipo: "nuevo" | "pagado"): string {
  const lines: string[] = []

  if (tipo === "nuevo") {
    lines.push("🛒 <b>NUEVO PEDIDO</b>")
  } else {
    lines.push("✅ <b>PAGO CONFIRMADO</b>")
  }
  lines.push(`Pedido: <b>${esc(order.id)}</b>`)
  lines.push(`📅 ${esc(order.fecha)}`)

  const metodo = METODO_PAGO_LABEL[order.metodo_pago] || order.metodo_pago || "?"
  const estado = ESTADO_LABEL[order.estado] || order.estado || "?"
  lines.push(`💳 ${metodo} · ${estado}`)
  if (order.metodo_pago_label) lines.push(`🏦 ${esc(order.metodo_pago_label)}`)

  lines.push("")
  lines.push("👤 <b>Cliente</b>")
  lines.push(`• ${esc(order.cliente.nombre)}`)
  if (order.cliente.email) lines.push(`• 📧 ${esc(order.cliente.email)}`)
  if (order.cliente.telefono) lines.push(`• 📱 ${esc(order.cliente.telefono)}`)
  if (order.cliente.dni) lines.push(`• DNI/CUIT: ${esc(order.cliente.dni)}`)
  if (order.cliente.metodo_envio === "retiro") {
    lines.push("• 🏬 Retiro en local")
  } else {
    if (order.cliente.direccion) lines.push(`• 🏠 ${esc(order.cliente.direccion)}`)
    if (order.cliente.ciudad) lines.push(`• 🗺️ ${esc(order.cliente.ciudad)}, ${esc(order.cliente.provincia)}`)
    if (order.cliente.zona_envio || order.cliente.velocidad_envio) {
      const zona = order.cliente.zona_envio ? esc(order.cliente.zona_envio) : ""
      const vel = order.cliente.velocidad_envio ? esc(order.cliente.velocidad_envio) : ""
      lines.push(`• 🚚 Envío: ${[zona, vel].filter(Boolean).join(" / ")}`)
    }
  }

  lines.push("")
  lines.push("📦 <b>Artículos</b>")
  for (const it of order.items || []) {
    const qty = it.quantity || 1
    const unit = fmtARS(it.price || 0)
    const sub = fmtARS((it.price || 0) * qty)
    lines.push(`• ${esc(it.name)}`)
    lines.push(`   SKU ${esc(it.sku)} · x${qty} · ${unit} = ${sub}`)
  }

  lines.push("")
  lines.push(`Subtotal: ${fmtARS(order.subtotal || 0)}`)
  lines.push(`Envío: ${order.envio ? fmtARS(order.envio) : "Gratis"}`)
  lines.push(`<b>TOTAL: ${fmtARS(order.total || 0)}</b>`)

  if (tipo === "pagado" && order.pago_ref) {
    lines.push("")
    lines.push(`🆔 Ref. pago: ${esc(order.pago_ref)}`)
  }

  return lines.join("\n")
}