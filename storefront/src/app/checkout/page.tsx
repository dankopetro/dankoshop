"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import {
  CreditCard,
  Landmark,
  Store,
  Truck,
  ShoppingBag,
  ArrowLeft,
  Loader2,
} from "lucide-react"
import {
  CartItem,
  Customer,
  formatARS,
  getCart,
  cartSubtotal,
  calcEnvio,
  saveOrder,
  clearCart,
  buildOrder,
  ENVIO_GRATIS_DESDE,
} from "@/lib/checkout"
import { getBankData } from "@/lib/banco"

const input =
  "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"

export default function CheckoutPage() {
  const router = useRouter()
  const [cart, setCart] = useState<CartItem[]>([])
  const [cliente, setCliente] = useState<Customer>({
    nombre: "",
    email: "",
    telefono: "",
    dni: "",
    direccion: "",
    ciudad: "",
    provincia: "Buenos Aires",
    metodo_envio: "retiro",
  })
  const [metodo, setMetodo] = useState<"mercadopago" | "transferencia">("mercadopago")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [enviando, setEnviando] = useState<null | "confirmar" | "pagar">(null)

  useEffect(() => {
    setCart(getCart())
  }, [])

  const subtotal = cartSubtotal(cart)
  const envio = calcEnvio(subtotal, cliente.metodo_envio)
  const total = subtotal + envio
  const banco = getBankData()

  const set = (k: keyof Customer, v: string) => setCliente((c) => ({ ...c, [k]: v }))

  const validar = useCallback((): string => {
    if (cart.length === 0) return "Tu carrito está vacío."
    if (!cliente.nombre.trim()) return "Ingresá tu nombre."
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(cliente.email)) return "Ingresá un email válido."
    if (cliente.telefono.trim().length < 8) return "Ingresá un teléfono válido."
    if (cliente.metodo_envio === "envio" && !cliente.direccion.trim())
      return "Ingresá la dirección de envío."
    return ""
  }, [cart, cliente])

  const persistir = useCallback(async (order: any) => {
    saveOrder(order)
    try {
      await fetch("/api/ordenes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order }),
      })
    } catch {
      // no bloquear el flujo
    }
  }, [])

  const confirmarTransferencia = async () => {
    const err = validar()
    if (err) return setError(err)
    setError("")
    setEnviando("confirmar")
    const order = buildOrder(cliente, cart, "transferencia", "pendiente")
    await persistir(order)
    clearCart()
    router.push(`/comprobante?ref=${order.id}`)
  }

  const pagarMercadoPago = async () => {
    const err = validar()
    if (err) return setError(err)
    setError("")
    setEnviando("pagar")

    // guardar el pedido con estado pendiente antes de redirigir
    const order = buildOrder(cliente, cart, "mercadopago", "pendiente")
    await persistir(order)

    try {
      const res = await fetch("/api/mercadopago/preference", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: cart.map((it) => ({ sku: it.sku, name: it.name, price: it.price, quantity: it.quantity })),
          external_reference: order.id,
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || "Error al iniciar el pago. Intentá de nuevo.")
        setEnviando(null)
        return
      }
      clearCart()
      const target = data.sandbox_init_point || data.init_point
      if (target) window.location.href = target
      else {
        setError("No se pudo obtener el link de pago.")
        setEnviando(null)
      }
    } catch (e) {
      setError(`Error: ${e instanceof Error ? e.message : String(e)}`)
      setEnviando(null)
    }
  }

  if (cart.length === 0 && enviando === null) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <ShoppingBag className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-xl font-medium text-gray-700 mb-2">No hay productos para el checkout</p>
        <Link href="/productos" className="inline-flex items-center bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700">
          Ver productos
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <Link href="/carrito" className="inline-flex items-center text-blue-600 hover:underline mb-6 text-sm">
        <ArrowLeft className="w-4 h-4 mr-1" /> Volver al carrito
      </Link>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Finalizar compra</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* Datos de contacto y envío */}
          <section className="bg-white p-6 rounded-xl border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-4">1. Tus datos</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre y apellido *</label>
                <input className={input} value={cliente.nombre} onChange={(e) => set("nombre", e.target.value)} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input className={input} type="email" value={cliente.email} onChange={(e) => set("email", e.target.value)} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono / WhatsApp *</label>
                <input className={input} value={cliente.telefono} onChange={(e) => set("telefono", e.target.value)} />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">DNI / CUIT</label>
                <input className={input} value={cliente.dni} onChange={(e) => set("dni", e.target.value)} />
              </div>
            </div>

            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <label className="flex items-center gap-3 border rounded-lg p-3 cursor-pointer">
                <input type="radio" name="envio" checked={cliente.metodo_envio === "retiro"} onChange={() => set("metodo_envio", "retiro")} />
                <Store className="w-5 h-5 text-gray-500" />
                <span className="text-sm">Retiro en Calle 26 N° 207, La Plata</span>
              </label>
              <label className="flex items-center gap-3 border rounded-lg p-3 cursor-pointer">
                <input type="radio" name="envio" checked={cliente.metodo_envio === "envio"} onChange={() => set("metodo_envio", "envio")} />
                <Truck className="w-5 h-5 text-gray-500" />
                <span className="text-sm">Envío a domicilio</span>
              </label>
            </div>

            {cliente.metodo_envio === "envio" && (
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Dirección *</label>
                  <input className={input} value={cliente.direccion} onChange={(e) => set("direccion", e.target.value)} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Ciudad</label>
                  <input className={input} value={cliente.ciudad} onChange={(e) => set("ciudad", e.target.value)} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Provincia</label>
                  <input className={input} value={cliente.provincia} onChange={(e) => set("provincia", e.target.value)} />
                </div>
              </div>
            )}
            {cliente.metodo_envio === "envio" && subtotal < ENVIO_GRATIS_DESDE && (
              <p className="text-xs text-gray-500 mt-2">
                Envío gratis a partir de {formatARS(ENVIO_GRATIS_DESDE)}.
              </p>
            )}
          </section>

          {/* Método de pago */}
          <section className="bg-white p-6 rounded-xl border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-4">2. Método de pago</h2>
            <div className="space-y-3">
              <label className="flex items-start gap-3 border rounded-lg p-4 cursor-pointer">
                <input type="radio" className="mt-1" checked={metodo === "mercadopago"} onChange={() => setMetodo("mercadopago")} />
                <div>
                  <div className="flex items-center gap-2 font-medium text-gray-900">
                    <CreditCard className="w-5 h-5 text-sky-600" /> Mercado Pago
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Tarjeta de crédito y débito, dinero en cuenta y efectivo (Rapipago / Pago Fácil / redes de cobranza).
                  </p>
                </div>
              </label>

              <label className="flex items-start gap-3 border rounded-lg p-4 cursor-pointer">
                <input type="radio" className="mt-1" checked={metodo === "transferencia"} onChange={() => setMetodo("transferencia")} />
                <div>
                  <div className="flex items-center gap-2 font-medium text-gray-900">
                    <Landmark className="w-5 h-5 text-green-600" /> Transferencia bancaria
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    Transferí a nuestra cuenta (Alias CVU) y te confirmamos el pedido al acreditarse.
                  </p>
                </div>
              </label>
            </div>

            {metodo === "transferencia" && (
              <div className="mt-4 bg-green-50 border border-green-200 rounded-lg p-4 text-sm space-y-1">
                <p className="font-semibold text-green-800">Datos para transferir:</p>
                <p>Titular: <span className="font-medium">{banco.titular}</span></p>
                <p>Banco: <span className="font-medium">{banco.banco}</span></p>
                <p>Alias CVU: <span className="font-medium break-all">{banco.alias}</span></p>
                <p>CBU: <span className="font-medium break-all">{banco.cbu}</span></p>
                <p>CUIT: <span className="font-medium">{banco.cuit}</span></p>
                <p className="text-xs text-green-700 pt-1">
                  Al confirmar, te generamos el comprobante de tu pedido. Guardá el n° de operación de tu banco si es posible.
                </p>
              </div>
            )}
          </section>
        </div>

        {/* Resumen */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 h-fit space-y-4 sticky top-4">
          <h3 className="text-xl font-bold text-gray-900">Resumen del pedido</h3>
          <div className="space-y-2 max-h-64 overflow-auto">
            {cart.map((it) => (
              <div key={it.sku} className="flex justify-between text-sm gap-2">
                <span className="text-gray-700 truncate">{it.name} <span className="text-gray-400">x{it.quantity}</span></span>
                <span className="text-gray-900 font-medium whitespace-nowrap">{formatARS((it.price || 0) * (it.quantity || 1))}</span>
              </div>
            ))}
          </div>
          <div className="border-t pt-3 space-y-1">
            <div className="flex justify-between text-sm text-gray-600"><span>Subtotal</span><span>{formatARS(subtotal)}</span></div>
            <div className="flex justify-between text-sm text-gray-600"><span>Envío</span><span>{envio === 0 ? "Gratis" : formatARS(envio)}</span></div>
            <div className="flex justify-between text-lg font-bold text-gray-900 border-t pt-2">
              <span>Total</span><span className="text-blue-600">{formatARS(total)}</span>
            </div>
          </div>

          {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-2">{error}</p>}

          {metodo === "mercadopago" ? (
            <button
              onClick={pagarMercadoPago}
              disabled={!!enviando}
              className="w-full bg-sky-600 hover:bg-sky-700 disabled:opacity-60 text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2 transition-colors"
            >
              {enviando === "pagar" ? <Loader2 className="w-5 h-5 animate-spin" /> : <CreditCard className="w-5 h-5" />}
              {enviando === "pagar" ? "Redirigiendo..." : "Pagar con Mercado Pago"}
            </button>
          ) : (
            <button
              onClick={confirmarTransferencia}
              disabled={!!enviando}
              className="w-full bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2 transition-colors"
            >
              {enviando === "confirmar" ? <Loader2 className="w-5 h-5 animate-spin" /> : <Landmark className="w-5 h-5" />}
              {enviando === "confirmar" ? "Generando..." : "Generar comprobante de transferencia"}
            </button>
          )}

          {metodo === "mercadopago" && (
            <p className="text-xs text-gray-500 text-center">
              Vas a continuar al entorno seguro de Mercado Pago.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
