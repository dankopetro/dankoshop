import { NextRequest, NextResponse } from "next/server"
import { getProducts } from "@/lib/medusa"

const KNOWLEDGE = require("@/content/mary.json") as {
  bienvenida: string
  saludo: string[]
  despedida: string[]
  no_entendido: string
  cuotas_interes: { descripcion: string; tasas: Record<string, number>; sin_interes_max: number }
  conocimiento: { keywords: string[]; answer: string }[]
}

function normalize(s: string): string {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
}

const SALUDOS = ["hola", "buenas", "buen dia", "buenas tardes", "buenas noches", "hey", "que tal", "mary"]
const DESPEDIDAS = ["chau", "adios", "gracias", "graciass", "ok", "perfecto", "listo", "hasta luego", "nos vemos"]

function formatPrice(n: number): string {
  return n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 })
}

function extractCuotas(msg: string): number | null {
  const match = msg.match(/(\d{1,2})\s*(?:cuota|cuotas|cuotitas|pagas)/)
  return match ? Number(match[1]) : null
}

function bestMatch(msg: string): { score: number; answer: string } {
  let best = { score: 0, answer: "" }
  for (const item of KNOWLEDGE.conocimiento) {
    let score = 0
    for (const kw of item.keywords) {
      if (msg.includes(normalize(kw))) score++
    }
    if (score > best.score) best = { score, answer: item.answer }
  }
  return best
}

const STOPWORDS = new Set([
  "cuota", "cuotas", "cuant", "cuanto", "cuanta", "cuantas", "precio", "precios",
  "cuesta", "cuestan", "cuesta", "vale", "sale", "salen", "tarjeta", "tarjetas",
  "credito", "interes", "en", "el", "la", "las", "los", "de", "con", "para",
  "me", "mi", "quiero", "necesito", "comprar", "pasar", "pasame", "digame",
  "digas", "podes", "podemos", "puedo", "hay", "tiene", "tienen", "tenes",
  "estoy", "estas", "cual", "cuales", "que", "cuales", "asi", "o", "u", "y",
])

function buscarKeywords(msg: string): string[] {
  return normalize(msg)
    .split(/[^a-z0-9]+/)
    .filter((w) => w.length > 2 && !STOPWORDS.has(w))
}

async function buscarProducto(msg: string): Promise<string | null> {
  const { products } = await getProducts({ limit: "1000" })
  const words = buscarKeywords(msg)

  let bestProduct: { name: string; score: number } | null = null
  for (const p of products) {
    let score = 0
    const name = normalize(p.name)
    for (const w of words) {
      if (name.includes(w)) score++
    }
    if (score > 0 && (!bestProduct || score > bestProduct.score)) {
      bestProduct = { name: p.name, score }
    }
  }
  return bestProduct && bestProduct.score >= 1 ? bestProduct.name : null
}

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}))
  const raw = String(body.message || "").trim()
  if (!raw) return NextResponse.json({ reply: KNOWLEDGE.bienvenida })

  const msg = normalize(raw)

  if (SALUDOS.some((s) => msg.includes(s))) {
    return NextResponse.json({ reply: KNOWLEDGE.saludo[Math.floor(Math.random() * KNOWLEDGE.saludo.length)] })
  }
  if (DESPEDIDAS.some((s) => msg.includes(s))) {
    return NextResponse.json({ reply: KNOWLEDGE.despedida[Math.floor(Math.random() * KNOWLEDGE.despedida.length)] })
  }

  const cuotas = extractCuotas(msg)
  const mentionsCuotas = msg.includes("cuota") || msg.includes("financi") || msg.includes("tarjeta") || msg.includes("interes")

  if (cuotas && mentionsCuotas) {
    const productName = await buscarProducto(msg)
    if (productName) {
      const { products } = await getProducts({ limit: "1000" })
      const product = products.find((p) => p.name === productName)
      if (product) {
        const precioBase =
          product.prices.precio_efectivo ??
          product.prices.precio_lista ??
          0
        if (precioBase > 0) {
          const tasa = KNOWLEDGE.cuotas_interes.tasas[String(cuotas)] ?? null
          if (tasa === null) {
            return NextResponse.json({
              reply: `Podés financiar "${productName}" en 3, 6, 9, 12 o 18 cuotas. Si me confirmás la cantidad, te paso el valor exacto. Hasta 6 cuotas es sin interés 😊`,
            })
          }
          if (tasa === 0) {
            const valor = Math.round(precioBase / cuotas)
            return NextResponse.json({
              reply: `El producto "${productName}" tiene un precio de ${formatPrice(precioBase)}. En ${cuotas} cuotas sin interés, pagás ${cuotas}x ${formatPrice(valor)}. 🎉`,
            })
          }
          const total = Math.round(precioBase * (1 + tasa))
          const valor = Math.round(total / cuotas)
          const extra = total - precioBase
          return NextResponse.json({
            reply: `El producto "${productName}" tiene un precio de ${formatPrice(precioBase)}. En ${cuotas} cuotas, se aplica un interés del ${Math.round(tasa * 100)}%, quedando un total de ${formatPrice(total)} (${formatPrice(extra)} de interés). Pagás ${cuotas}x ${formatPrice(valor)}.`,
          })
        }
      }
    }
  }

  const productName = await buscarProducto(msg)
  if (productName) {
    const { products } = await getProducts({ limit: "1000" })
    const product = products.find((p) => p.name === productName)
    if (product) {
      const efectivo =
        product.prices.precio_efectivo ??
        product.prices.precio_lista ??
        0
      const lista = product.prices.precio_lista ?? 0
      if (efectivo > 0) {
        const extra = lista > efectivo ? ` (listado en ${formatPrice(lista)})` : ""
        return NextResponse.json({
          reply: `"${productName}" tiene un precio de ${formatPrice(efectivo)}${extra}. Pagando con tarjeta podés hacerlo en hasta 6 cuotas sin interés. ¿Querés que te calcule las cuotas? 😊`,
        })
      }
    }
  }

  if (mentionsCuotas && cuotas) {
    return NextResponse.json({
      reply: `Te ayudo con las cuotas 😊. Aceptamos tarjetas de crédito con hasta 6 cuotas sin interés. A partir de 9 cuotas se aplica interés según la promoción vigente. Si me decís qué producto te interesa, te calculo el valor exacto.`,
    })
  }

  const match = bestMatch(msg)
  if (match.score > 0) {
    return NextResponse.json({ reply: match.answer })
  }

  return NextResponse.json({ reply: KNOWLEDGE.no_entendido })
}
