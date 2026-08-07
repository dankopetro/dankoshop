"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { ShoppingCart } from "lucide-react"
import { getCart } from "@/lib/checkout"

export default function CartIcon() {
  const [count, setCount] = useState(0)

  useEffect(() => {
    const update = () => {
      const items = getCart()
      setCount(items.reduce((acc, i) => acc + (i.quantity || 1), 0))
    }
    update()
    window.addEventListener("dankoshop_cart_update", update)
    window.addEventListener("storage", update)
    return () => {
      window.removeEventListener("dankoshop_cart_update", update)
      window.removeEventListener("storage", update)
    }
  }, [])

  return (
    <Link href="/carrito" className="relative p-2 text-gray-600 hover:text-gray-900">
      <ShoppingCart className="w-6 h-6" />
      {count > 0 && (
        <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
          {count}
        </span>
      )}
    </Link>
  )
}
