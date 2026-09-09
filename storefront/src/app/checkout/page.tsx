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
  saveOrder,
  clearCart,
  buildOrder,
} from "@/lib/checkout"
import { getBankData } from "@/lib/banco"
import { ZONAS_ENVIO, ENVIO_GRATIS_DESDE, calcEnvioCosto, EnvioZona, EnvioVelocidad } from "@/lib/envios"

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
    zona_envio: "laplata",
    velocidad_envio: "estandar",
  })
  const [metodo, setMetodo] = useState<"mercadopago" | "transferencia">("mercadopago")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [enviando, setEnviando] = useState<null | "confirmar" | "pagar">(null)
  const [stockError, setStockError] = useState<string[]>([])

  useEffect(() => {
    setCart(getCart())
  }, [])

  const getItemPrice = useCallback((it: CartItem, m: "mercadopago" | "transferencia") => {
    if (m === "mercadopago" && typeof it.price_lista === "number" && it.price_lista > 0) {
      return it.price_lista
    }
    return it.price
  }, [])

  const subtotal = cart.reduce((acc, it) => acc + getItemPrice(it, metodo) * (it.quantity || 1), 0)
  const hasBigItems = cart.some((it) => it.envio_grande)
  const envio = cliente.metodo_envio === "retiro" ? 0 : hasBigItems && cliente.metodo_envio === "envio" ? 0 : calcEnvioCosto(subtotal, cliente.zona_envio || null, cliente.velocidad_envio || "estandar")
  const total = subtotal + envio
  const banco = getBankData()

  const set = (k: keyof Customer, v: string) => setCliente((c) => ({ ...c, [k]: v }))

  const validarStock = useCallback(async (): Promise<boolean> => {
    const sinStock: string[] = []

    try {
      const res = await fetch("/api/check-stock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ skus: cart.map((i) => i.sku) }),
      })
      if (res.ok) {
        const data = await res.json()
        for (const item of cart) {
          const stockLevel = data.stock?.[item.sku]
          if (stockLevel === 0) {
            sinStock.push(item.name)
          }
        }
      }
    } catch {}

    if (sinStock.length > 0) {
      setStockError(sinStock)
      return false
    }
    setStockError([])
    return true
  }, [cart])

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
    const stockOk = await validarStock()
    if (!stockOk) return setError("Algunos productos sin stock. Volvé al carrito y eliminalos.")
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
    const stockOk = await validarStock()
    if (!stockOk) return setError("Algunos productos sin stock. Volvé al carrito y eliminalos.")
    setEnviando("pagar")

    // guardar el pedido con estado pendiente antes de redirigir
    const order = buildOrder(cliente, cart, "mercadopago", "pendiente")
    await persistir(order)

    try {
      const res = await fetch("/api/mercadopago/preference", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: cart.map((it) => ({
            sku: it.sku,
            name: it.name,
            price: getItemPrice(it, "mercadopago"),
            quantity: it.quantity,
            description: it.name,
          })),
          external_reference: order.id,
          payer: {
            nombre: cliente.nombre,
            email: cliente.email,
            telefono: cliente.telefono,
            dni: cliente.dni,
            direccion: cliente.direccion,
            ciudad: cliente.ciudad,
            provincia: cliente.provincia,
          },
        }),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.error || "Error al iniciar el pago. Intentá de nuevo.")
        setEnviando(null)
        return
      }
      clearCart()
      const target = data.init_point || data.sandbox_init_point
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
                <span className="text-sm">Retiro en local (a coordinar)</span>
              </label>
              {!hasBigItems && (
                <label className="flex items-center gap-3 border rounded-lg p-3 cursor-pointer">
                  <input type="radio" name="envio" checked={cliente.metodo_envio === "envio"} onChange={() => set("metodo_envio", "envio")} />
                  <Truck className="w-5 h-5 text-gray-500" />
                  <span className="text-sm">Envío a domicilio</span>
                </label>
              )}
              {hasBigItems && (
                <div className="border rounded-lg p-3 bg-amber-50 border-amber-200">
                  <div className="flex items-center gap-2 text-amber-700">
                    <Truck className="w-5 h-5" />
                    <span className="text-sm font-medium">Envío de productos grandes</span>
                  </div>
                  <p className="text-xs text-amber-600 mt-1">
                    El envío de productos de gran volumen se coordina después de la compra. Te contactamos para definir costo y plazo.
                  </p>
                </div>
              )}
            </div>

            {cliente.metodo_envio === "retiro" && (
              <p className="text-xs text-gray-500 mt-2">
                El stock se confirma después de la compra. Puede tardar entre 5 y 7 días hábiles en estar disponible para retirar.
              </p>
            )}

            {cliente.metodo_envio === "envio" && !hasBigItems && (
              <div className="mt-4 space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Zona de envío *</label>
                    <select
                      className={input}
                      value={cliente.zona_envio || "laplata"}
                      onChange={(e) => set("zona_envio", e.target.value as EnvioZona)}
                    >
                      {ZONAS_ENVIO.map((z) => (
                        <option key={z.zona} value={z.zona}>{z.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Velocidad *</label>
                    <select
                      className={input}
                      value={cliente.velocidad_envio || "estandar"}
                      onChange={(e) => set("velocidad_envio", e.target.value as EnvioVelocidad)}
                    >
                      <option value="estandar">Estándar (5-7 días)</option>
                      <option value="express">Express (2-3 días)</option>
                    </select>
                  </div>
                </div>

                {subtotal >= 200000 ? (
                  <p className="text-sm text-green-600 font-medium">
                    🎉 Envío gratis por superar {formatARS(200000)}
                  </p>
                ) : subtotal >= 100000 ? (
                  <p className="text-sm text-blue-600 font-medium">
                    ✨ 50% OFF en envío por superar {formatARS(100000)}
                  </p>
                ) : (
                  <p className="text-sm text-gray-600">
                    Costo de envío: <span className="font-medium">{formatARS(envio)}</span>
                    {cliente.velocidad_envio === "express" ? " (express)" : " (estándar)"}
                  </p>
                )}
              </div>
            )}
            {hasBigItems && (
              <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-700">
                <p className="font-medium mb-1">Envío de productos grandes</p>
                <p>Dentro de La Plata, Berisso y Ensenada coordinamos el envío sin costo adicional en compras mayores a {formatARS(100000)}.</p>
                <p className="mt-1">Fuera de esta zona, el costo es similar al de un flete. Te contactamos después de la compra para coordinar.</p>
              </div>
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
                <span className="text-gray-900 font-medium whitespace-nowrap">{formatARS(getItemPrice(it, metodo) * (it.quantity || 1))}</span>
              </div>
            ))}
          </div>
          <div className="border-t pt-3 space-y-1">
            <div className="flex justify-between text-sm text-gray-600"><span>Subtotal</span><span>{formatARS(subtotal)}</span></div>
            <div className="flex justify-between text-sm text-gray-600"><span>Envío</span><span>{hasBigItems ? (cliente.metodo_envio === "retiro" ? "Gratis" : "A coordinar") : (envio === 0 ? "Gratis" : formatARS(envio))}</span></div>
            {!hasBigItems && cliente.metodo_envio === "envio" && envio > 0 && (
              <p className="text-xs text-gray-400 text-right">{cliente.velocidad_envio === "express" ? "Express" : "Estándar"} - {ZONAS_ENVIO.find(z => z.zona === cliente.zona_envio)?.label}</p>
            )}
            <div className="flex justify-between text-lg font-bold text-gray-900 border-t pt-2">
              <span>Total</span><span className="text-blue-600">{formatARS(total)}</span>
            </div>
          </div>

          {error && <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-2">{error}</p>}
          {stockError.length > 0 && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-2">
              <p className="font-semibold mb-1">Sin stock:</p>
              <ul className="list-disc list-inside">{stockError.map((n) => <li key={n}>{n}</li>)}</ul>
            </div>
          )}

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
