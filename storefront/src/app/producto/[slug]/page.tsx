import { getProduct } from "@/lib/medusa"
import { notFound } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Truck, Shield, CreditCard } from "lucide-react"
import ProductImage from "@/components/product-image"
import AddToCart from "@/components/add-to-cart"

function formatPrice(n: number | null) {
  if (n === null) return null
  return n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 })
}

export default async function ProductoPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const product = await getProduct(slug)
  if (!product) notFound()

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link href="/productos" className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-6">
          <ArrowLeft className="w-4 h-4" />
          Volver al catálogo
        </Link>

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
            <div className="relative">
              {product.images.length > 0 ? (
                <ProductImage
                  images={product.images}
                  name={product.name}
                  className="h-72 lg:h-[500px]"
                />
              ) : (
                <div className="h-72 lg:h-[500px] bg-gray-100 flex items-center justify-center text-8xl">
                  📦
                </div>
              )}
              {product.images.length > 1 && (
                <div className="absolute bottom-3 left-3 bg-black/60 text-white text-xs px-2 py-1 rounded">
                  📷 {product.images.length} fotos — Click para ampliar
                </div>
              )}
            </div>

            <div className="p-6 lg:p-8">
              <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">{product.name}</h1>
              <p className="text-sm text-gray-400 mt-1">SKU: {product.sku}</p>

              <div className="mt-6 space-y-2">
                {product.prices.precio_lista && (
                  <p className="text-sm text-gray-400 line-through">
                    Precio lista: {formatPrice(product.prices.precio_lista)}
                  </p>
                )}
                {product.prices.precio_efectivo && (
                  <p className="text-3xl font-bold text-green-600">
                    {formatPrice(product.prices.precio_efectivo)}
                  </p>
                )}
                {product.prices.precio_transferencia && (
                  <p className="text-sm text-gray-600">
                    Transferencia: <span className="font-semibold">{formatPrice(product.prices.precio_transferencia)}</span>
                  </p>
                )}
                {product.prices.cuota_valor_3 && (
                  <p className="text-sm text-blue-600 font-medium">
                    3x {formatPrice(product.prices.cuota_valor_3)} sin interés
                  </p>
                )}
                {product.prices.cuota_valor_6 && (
                  <p className="text-sm text-blue-600 font-medium">
                    6x {formatPrice(product.prices.cuota_valor_6)} sin interés
                  </p>
                )}
                {product.prices.cuota_valor_12 && (
                  <p className="text-sm text-blue-600 font-medium">
                    12x {formatPrice(product.prices.cuota_valor_12)} con interés
                  </p>
                )}
              </div>

              {product.description && (
                <div className="mt-6 pt-6 border-t border-gray-100">
                  <h3 className="font-semibold text-gray-900 mb-2">Descripción</h3>
                  <p className="text-sm text-gray-600 whitespace-pre-line">{product.description}</p>
                </div>
              )}

              <div className="mt-8 pt-6 border-t border-gray-100">
                <AddToCart product={product} />
              </div>

              <div className="mt-6 pt-6 border-t border-gray-100 space-y-3">
                <div className="flex items-center gap-3 text-sm text-gray-600">
                  <Truck className="w-5 h-5 text-blue-500" />
                  Envío gratis en compras +$50.000
                </div>
                <div className="flex items-center gap-3 text-sm text-gray-600">
                  <Shield className="w-5 h-5 text-blue-500" />
                  Compra 100% segura
                </div>
                <div className="flex items-center gap-3 text-sm text-gray-600">
                  <CreditCard className="w-5 h-5 text-blue-500" />
                  Aceptamos todos los medios de pago
                </div>
              </div>
            </div>
          </div>
        </div>

        {product.images.length > 1 && (
          <div className="mt-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Más imágenes</h3>
            <div className="grid grid-cols-4 sm:grid-cols-6 lg:grid-cols-8 gap-3">
              {product.images.map((img, i) => (
                <ProductImage
                  key={i}
                  images={product.images}
                  name={product.name}
                  className="h-20"
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
