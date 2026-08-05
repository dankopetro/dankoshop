"use client"

import Image from "next/image"
import Link from "next/link"
import { format } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ShoppingCart, Tag, CreditCard, Banknote, Users } from "lucide-react"
import { Product } from "@/types"

interface ProductCardProps {
  product: Product
}

export default function ProductCard({ product }: ProductCardProps) {
  const precioLista = product.metadata?.precio_lista || product.variants[0]?.prices[0]?.amount || 0
  const precioEfectivo = product.metadata?.precio_efectivo || Math.round(precioLista * 0.85)
  const precioTransferencia = product.metadata?.precio_transferencia || Math.round(precioLista * 0.90)
  const cuotas = product.metadata?.cuotas || 3
  const cuotaValor = product.metadata?.cuota_valor || Math.round(precioLista / 3)
  
  const imageUrl = product.thumbnail || product.images[0]?.url

  return (
    <Link href={`/producto/${product.handle}`} className="group">
      <Card className="h-full bg-white border-gray-200 hover:border-blue-300 hover:shadow-lg transition-all duration-300 overflow-hidden">
        {/* Image */}
        <CardHeader className="p-0 relative aspect-square overflow-hidden bg-gray-50">
          {imageUrl ? (
            <Image
              src={imageUrl}
              alt={product.title}
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
          {/* Badges */}
          <div className="absolute top-2 left-2 flex flex-col gap-1">
            {product.metadata?.precio_lista && (
              <Badge variant="secondary" className="text-xs">Lista: ${format(product.metadata.precio_lista)}</Badge>
            )}
            {product.metadata?.precio_efectivo && (
              <Badge className="bg-green-600 text-white text-xs">
                <Banknote className="w-3 h-3 mr-1" />
                Efectivo: ${format(product.metadata.precio_efectivo)}
              </Badge>
            )}
            {product.metadata?.precio_mayorista && (
              <Badge variant="outline" className="text-xs">
                <Users className="w-3 h-3 mr-1" />
                Mayorista: ${format(product.metadata.precio_mayorista)}
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="p-4">
          {/* Category */}
          {product.categories?.[0] && (
            <Badge variant="outline" className="text-xs mb-2">
              {product.categories[0].name}
            </Badge>
          )}
          
          <h3 className="font-medium text-gray-900 line-clamp-2 mb-2 group-hover:text-blue-600 transition-colors">
            {product.title}
          </h3>
          
          {/* SKU */}
          {product.variants[0]?.sku && (
            <p className="text-xs text-gray-500 mb-2">SKU: {product.variants[0].sku}</p>
          )}

          {/* Prices */}
          <div className="space-y-1 mb-4">
            {precioLista && (
              <div className="flex items-center gap-2">
                <span className="text-lg font-bold text-gray-900">${format(precioLista)}</span>
                {precioEfectivo < precioLista && (
                  <span className="text-sm text-gray-500 line-through">${format(precioEfectivo)}</span>
                )}
              </div>
            )}
            {precioEfectivo && precioEfectivo < precioLista && (
              <div className="flex items-center gap-2 text-green-600 font-medium">
                <Banknote className="w-4 h-4" />
                <span>Efectivo/Transferencia: ${format(precioEfectivo)}</span>
                <Badge variant="secondary" className="text-xs ml-auto">15% OFF</Badge>
              </div>
            )}
            {precioTransferencia && precioTransferencia !== precioEfectivo && (
              <div className="flex items-center gap-2 text-blue-600 font-medium text-sm">
                <CreditCard className="w-4 h-4" />
                <span>Transferencia: ${format(precioTransferencia)}</span>
                <Badge variant="secondary" className="text-xs ml-auto">10% OFF</Badge>
              </div>
            )}
            {cuotas && cuotaValor && (
              <div className="flex items-center gap-2 text-gray-600 text-sm">
                <Tag className="w-4 h-4" />
                <span>{cuotas} cuotas sin interés de ${format(cuotaValor)}</span>
              </div>
            )}
          </div>
        </CardContent>

        <CardFooter className="p-4 pt-0 border-t border-gray-100">
          <Button className="w-full" size="sm">
            <ShoppingCart className="w-4 h-4 mr-2" />
            Ver producto
          </Button>
        </CardFooter>
      </Card>
    </Link>
  )
}