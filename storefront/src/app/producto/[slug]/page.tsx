import { products } from "@/data/products"
import { notFound } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Truck, Shield, CreditCard } from "lucide-react"

function formatPrice(n: number | null) {
  if (n === null) return null
  return n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 })
}

const categoryIcons: Record<string, string> = {
  "Accesorios": "🎒", "Bicicletas": "🚲", "Celulares": "📱", "Cocinas/Hornos/Microondas": "🍳",
  "Combos": "📦", "Deportes": "⚽", "Gaming": "🎮", "Heladeras/Freezers": "❄️",
  "Herramientas": "🔧", "Hogar/Baño": "🛁", "Lavarropas/Secarropas": "🌀",
  "Outdoor/Playa": "🏖️", "Pequeños Electrodomésticos": "🍳", "TVs": "📺",
  "Tablets": "📱", "Varios": "📦",
}

export function generateStaticParams() {
  return products.map((p) => ({ slug: p.slug }))
}

export default async function ProductoPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const product = products.find((p) => p.slug === slug)
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
            <div className="h-72 lg:h-[500px] bg-gray-100 flex items-center justify-center text-8xl">
              {categoryIcons[product.category] || "📦"}
            </div>

            <div className="p-6 lg:p-8">
              <span className="text-sm text-blue-600 font-medium">{product.category}</span>
              <h1 className="text-2xl lg:text-3xl font-bold text-gray-900 mt-2">{product.name}</h1>
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
                {product.prices.precio_mayorista && (
                  <p className="text-sm text-gray-600">
                    Mayorista (3+): <span className="font-semibold">{formatPrice(product.prices.precio_mayorista)}</span>
                  </p>
                )}
                {product.prices.cuotas && product.prices.cuota_valor && (
                  <p className="text-sm text-blue-600 font-medium">
                    {product.prices.cuotas}x {formatPrice(product.prices.cuota_valor)} sin interés
                  </p>
                )}
              </div>

              {product.description && (
                <div className="mt-6 pt-6 border-t border-gray-100">
                  <h3 className="font-semibold text-gray-900 mb-2">Descripción</h3>
                  <p className="text-sm text-gray-600 whitespace-pre-line">{product.description}</p>
                </div>
              )}

              <div className="mt-8 pt-6 border-t border-gray-100 space-y-3">
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
      </div>
    </div>
  )
}
