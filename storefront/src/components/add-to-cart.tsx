"use client"

import { useState } from "react"
import { ShoppingCart, Check } from "lucide-react"
import { getCart, saveCart } from "@/lib/checkout"
import { Product } from "@/lib/medusa"

interface AddToCartProps {
  product: Product
}

export default function AddToCart({ product }: AddToCartProps) {
  const [qty, setQty] = useState(1)
  const [added, setAdded] = useState(false)

  const outOfStock = product.stock === 0
  const lowStock = product.stock !== null && product.stock > 0 && product.stock <= 5

  const priceEfectivo =
    product.prices.precio_efectivo ??
    product.prices.precio_lista ??
    0

  const priceLista = product.prices.precio_lista ?? priceEfectivo

  const handleAdd = () => {
    if (outOfStock) return
    const items = getCart()
    const existing = items.find((i) => i.sku === product.sku)
    if (existing) {
      existing.quantity = (existing.quantity || 1) + qty
      existing.price = priceEfectivo
      existing.price_lista = priceLista
    } else {
      items.push({
        sku: product.sku,
        name: product.name,
        price: priceEfectivo,
        price_lista: priceLista,
        quantity: qty,
        image: product.images[0],
        envio_grande: product.envio_grande,
      })
    }
    saveCart(items)
    window.dispatchEvent(new Event("dankoshop_cart_update"))
    setAdded(true)
    setTimeout(() => setAdded(false), 1500)
  }

  if (outOfStock) {
    return (
      <div className="flex flex-col gap-2">
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-100 text-red-700 text-sm font-semibold rounded-full w-fit">
          Sin stock
        </span>
        <button disabled className="flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-medium bg-gray-300 text-gray-500 cursor-not-allowed">
          <ShoppingCart className="w-5 h-5" />
          No disponible
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {lowStock && (
        <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-100 text-amber-700 text-sm font-semibold rounded-full w-fit">
          Quedan {product.stock} unidades
        </span>
      )}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex items-center border border-gray-300 rounded-lg">
          <button
            onClick={() => setQty((q) => Math.max(1, q - 1))}
            className="w-10 h-11 text-lg text-gray-600 hover:bg-gray-100 rounded-l-lg"
          >
            −
          </button>
          <span className="w-10 text-center font-medium">{qty}</span>
          <button
            onClick={() => setQty((q) => Math.min(product.stock ?? 999, q + 1))}
            className="w-10 h-11 text-lg text-gray-600 hover:bg-gray-100 rounded-r-lg"
          >
            +
          </button>
        </div>

        <button
          onClick={handleAdd}
          className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-colors ${
            added ? "bg-green-600 text-white" : "bg-blue-600 hover:bg-blue-700 text-white"
          }`}
        >
          {added ? <Check className="w-5 h-5" /> : <ShoppingCart className="w-5 h-5" />}
          {added ? "Agregado al carrito" : "Agregar al carrito"}
        </button>
      </div>
    </div>
  )
}
