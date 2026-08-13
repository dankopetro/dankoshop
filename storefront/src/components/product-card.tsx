"use client"

import Image from "next/image"
import Link from "next/link"
import { Banknote, Tag } from "lucide-react"
import { Product } from "@/lib/medusa"

interface ProductCardProps {
  product: Product
}

export default function ProductCard({ product }: ProductCardProps) {
  const { prices } = product
  const precioLista = prices.precio_lista || 0
  const precioEfectivo = prices.precio_efectivo || 0
  const cuotaValor3 = prices.cuota_valor_3 || 0
  const cuotaValor6 = prices.cuota_valor_6 || 0
  const cuotaValor12 = prices.cuota_valor_12 || 0

  return (
    <Link href={`/producto/${product.slug}`} className="group">
      <div className="h-full bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-lg transition-all duration-300 overflow-hidden">
        <div className="p-0 relative aspect-square overflow-hidden bg-gray-50">
          {product.images.length > 0 ? (
            <Image
              src={product.images[0]}
              alt={product.name}
              fill
              className="object-cover group-hover:scale-105 transition-transform duration-300"
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
              <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          )}
          {precioEfectivo > 0 && (
            <div className="absolute top-2 left-2 flex flex-col gap-1">
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-600 text-white">
                <Banknote className="w-3 h-3 mr-1" />
                Efectivo / Débito
              </span>
            </div>
          )}
        </div>

        <div className="p-4">
          <span className="inline-block px-2 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded-full mb-2">
            {product.category}
          </span>

          <h3 className="font-medium text-gray-900 line-clamp-2 mb-2 group-hover:text-blue-600">
            {product.name}
          </h3>

          {product.sku && (
            <p className="text-xs text-gray-500 mb-2">SKU: {product.sku}</p>
          )}

          <div className="space-y-1 mb-4">
            {precioLista > 0 && (
              <div className="text-lg font-bold text-gray-900">
                ${precioLista.toLocaleString("es-AR")}
              </div>
            )}
            {precioEfectivo > 0 && precioEfectivo < precioLista && (
              <div className="flex items-center gap-2 text-green-600 font-medium text-sm">
                <Banknote className="w-4 h-4" />
                <span>Efectivo / Débito: ${precioEfectivo.toLocaleString("es-AR")}</span>
              </div>
            )}
            {cuotaValor3 > 0 && (
              <div className="flex items-center gap-2 text-gray-600 text-sm">
                <Tag className="w-4 h-4" />
                <span>3 cuotas de ${cuotaValor3.toLocaleString("es-AR")}</span>
              </div>
            )}
            {cuotaValor6 > 0 && (
              <div className="flex items-center gap-2 text-gray-600 text-sm">
                <Tag className="w-4 h-4" />
                <span>6 cuotas de ${cuotaValor6.toLocaleString("es-AR")}</span>
              </div>
            )}
            {cuotaValor12 > 0 && (
              <div className="flex items-center gap-2 text-gray-600 text-sm">
                <Tag className="w-4 h-4" />
                <span>12 cuotas de ${cuotaValor12.toLocaleString("es-AR")}</span>
              </div>
            )}
          </div>

          <button className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors">
            Ver producto
          </button>
        </div>
      </div>
    </Link>
  )
}
