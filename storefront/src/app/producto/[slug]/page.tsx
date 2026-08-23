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

              {product.stock === 0 && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-red-100 text-red-700 text-sm font-semibold rounded-full mt-2">
                  Sin stock
                </span>
              )}
              {product.stock !== null && product.stock > 0 && product.stock <= 5 && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-amber-100 text-amber-700 text-sm font-semibold rounded-full mt-2">
                  Quedan {product.stock} unidades
                </span>
              )}

              <div className="mt-6 space-y-3 p-4 bg-gray-50 rounded-xl border border-gray-200">
                {product.prices.precio_efectivo && (
                  <div>
                    <span className="inline-block bg-green-100 text-green-800 text-xs font-semibold px-2.5 py-0.5 rounded-full mb-1">
                      💵 Precio Efectivo / Transferencia / Débito
                    </span>
                    <p className="text-3xl font-extrabold text-green-600">
                      {formatPrice(product.prices.precio_efectivo)}
                    </p>
                  </div>
                )}
                {product.prices.precio_lista && (
                  <div className="pt-2 border-t border-gray-200">
                    <p className="text-sm font-semibold text-gray-700">
                      💳 Precio de Lista (Crédito): <span className="text-base text-gray-900 font-bold">{formatPrice(product.prices.precio_lista)}</span>
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Aceptamos tarjetas de crédito en hasta 12 cuotas fijas o según las promociones de tu banco en Mercado Pago.
                    </p>
                  </div>
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
