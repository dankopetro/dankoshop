"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Trash2, ShoppingBag, ArrowRight, AlertTriangle } from "lucide-react"

export default function CarritoPage() {
  const router = useRouter()
  const [cart, setCart] = useState<any[]>([])
  const [stockWarnings, setStockWarnings] = useState<Record<string, number>>({})
  const [checkingStock, setCheckingStock] = useState(false)

  useEffect(() => {
    // Load cart from localStorage or event
    const saved = localStorage.getItem("dankoshop_cart")
    if (saved) {
      try { setCart(JSON.parse(saved)) } catch(e) {}
    }
  }, [])

  useEffect(() => {
    if (cart.length === 0) return
    setCheckingStock(true)
    const skus = cart.map((i: any) => i.sku).filter(Boolean)
    if (skus.length === 0) { setCheckingStock(false); return }

    const backendUrl = process.env.NEXT_PUBLIC_MEDUSA_BACKEND_URL || "http://localhost:9000"
    const pk = process.env.NEXT_PUBLIC_MEDUSA_PUBLISHABLE_KEY || ""

    Promise.all(
      skus.map(async (sku: string) => {
        try {
          const res = await fetch(`${backendUrl}/store/products?q=${sku}&limit=5`, {
            headers: pk ? { "x-publishable-api-key": pk } : {},
          })
          if (!res.ok) return
          const data = await res.json()
          const match = (data.products || []).find((p: any) =>
            p.variants?.some((v: any) => v.sku === sku)
          )
          if (match) {
            const inv = match.variants?.[0]?.inventory_quantity
            if (inv !== undefined && inv !== null) {
              return { sku, stock: inv }
            }
          }
        } catch {}
        return null
      })
    ).then((results) => {
      const map: Record<string, number> = {}
      for (const r of results) {
        if (r) map[r.sku] = r.stock
      }
      setStockWarnings(map)
      setCheckingStock(false)
    })
  }, [cart])

  const removeItem = (sku: string) => {
    const updated = cart.filter(item => item.sku !== sku)
    setCart(updated)
    localStorage.setItem("dankoshop_cart", JSON.stringify(updated))
    setStockWarnings((prev) => {
      const next = { ...prev }
      delete next[sku]
      return next
    })
  }

  const clearCart = () => {
    setCart([])
    localStorage.removeItem("dankoshop_cart")
    setStockWarnings({})
  }

  const total = cart.reduce((acc, item) => acc + (item.price || 0) * (item.quantity || 1), 0)

  const hasOutOfStock = Object.values(stockWarnings).some((s) => s === 0)

  const checkoutWhatsApp = () => {
    const itemsList = cart.map(i => `- ${i.name} (SKU: ${i.sku}) x${i.quantity || 1} - $%s`.replace("%s", (i.price || 0).toLocaleString("es-AR"))).join("%0A")
    const text = `Hola DankoShop! Quiero realizar el siguiente pedido:%0A%0A${itemsList}%0A%0A*Total: $${total.toLocaleString("es-AR")}.*%0A%0AMi dirección de envío o coordinamos retiro:`
    window.open(`https://wa.me/5492216219596?text=${text}`, "_blank")
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Carrito de Compras</h1>
      {cart.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <ShoppingBag className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <p className="text-xl font-medium text-gray-700 mb-2">Tu carrito está vacío</p>
          <p className="text-gray-500 mb-6">Explorá nuestro catálogo y encontrá lo que buscás.</p>
          <Link href="/productos" className="inline-flex items-center bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-medium transition-colors">
            Ver productos
            <ArrowRight className="w-4 h-4 ml-2" />
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-4">
            {cart.map(item => (
              <div key={item.sku} className="flex items-center justify-between bg-white p-4 rounded-xl border border-gray-200">
                <div className="flex items-center gap-4">
                  {item.image && <img src={item.image} alt={item.name} className="w-20 h-20 object-cover rounded-lg" />}
                  <div>
                    <h3 className="font-medium text-gray-900">{item.name}</h3>
                    <p className="text-sm text-gray-500">SKU: {item.sku}</p>
                    {stockWarnings[item.sku] === 0 && (
                      <span className="inline-flex items-center gap-1 text-xs text-red-600 font-semibold mt-1">
                        <AlertTriangle className="w-3 h-3" /> Sin stock
                      </span>
                    )}
                    {stockWarnings[item.sku] !== undefined && stockWarnings[item.sku] > 0 && stockWarnings[item.sku] <= 5 && (
                      <span className="text-xs text-amber-600 font-medium mt-1 block">
                        Quedan {stockWarnings[item.sku]} unidades
                      </span>
                    )}
                    <p className="text-blue-600 font-semibold mt-1">${(item.price || 0).toLocaleString("es-AR")}</p>
                  </div>
                </div>
                <button onClick={() => removeItem(item.sku)} className="text-red-500 hover:text-red-700 p-2">
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            ))}
            <button onClick={clearCart} className="text-sm text-gray-500 hover:text-gray-700 underline">
              Vaciar carrito
            </button>
          </div>
          <div className="bg-white p-6 rounded-xl border border-gray-200 h-fit space-y-4">
            <h3 className="text-xl font-bold text-gray-900">Resumen del pedido</h3>
            <div className="flex justify-between text-lg font-semibold text-gray-900 border-t pt-4">
              <span>Total:</span>
              <span className="text-blue-600">${total.toLocaleString("es-AR")}</span>
            </div>
            {hasOutOfStock && (
              <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg p-2">
                Hay productos sin stock. Eliminalos del carrito para continuar.
              </p>
            )}
            <button onClick={checkoutWhatsApp} disabled={hasOutOfStock} className="w-full bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2 transition-colors">
              Finalizar compra por WhatsApp 📲
            </button>
            <button onClick={() => router.push("/checkout")} disabled={hasOutOfStock} className="w-full bg-sky-600 hover:bg-sky-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2 transition-colors">
              Continuar al checkout (pagos online) →
            </button>
            <p className="text-xs text-center text-gray-500">Retirá en nuestro local o pedí envío a domicilio.</p>
          </div>
        </div>
      )}
    </div>
  )
}
