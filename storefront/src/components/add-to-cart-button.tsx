"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { ShoppingCart, Plus, Minus, Check } from "lucide-react"

interface AddToCartButtonProps {
  product: any
}

export default function AddToCartButton({ product }: AddToCartButtonProps) {
  const [quantity, setQuantity] = useState(1)
  const [added, setAdded] = useState(false)

  const handleAddToCart = () => {
    // TODO: Implement cart logic with Medusa
    setAdded(true)
    setTimeout(() => setAdded(false), 2000)
  }

  return (
    <div className="space-y-3">
      {/* Quantity selector */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-600">Cantidad:</span>
        <div className="flex items-center border border-gray-300 rounded-lg">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setQuantity(Math.max(1, quantity - 1))}
          >
            <Minus className="w-4 h-4" />
          </Button>
          <span className="w-12 text-center font-medium">{quantity}</span>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setQuantity(quantity + 1)}
          >
            <Plus className="w-4 h-4" />
          </Button>
        </div>
        {quantity >= 3 && (
          <span className="text-xs text-purple-600 font-medium">¡Precio mayorista!</span>
        )}
      </div>

      {/* Add to cart */}
      <Button
        size="lg"
        className="w-full py-3 text-lg"
        onClick={handleAddToCart}
        disabled={added}
      >
        {added ? (
          <>
            <Check className="w-5 h-5 mr-2" />
            ¡Agregado al carrito!
          </>
        ) : (
          <>
            <ShoppingCart className="w-5 h-5 mr-2" />
            Agregar al carrito
          </>
        )}
      </Button>
    </div>
  )
}