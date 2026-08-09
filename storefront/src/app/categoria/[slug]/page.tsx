import { getCategories, getProducts } from "@/lib/medusa"
import { notFound } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, ArrowRight } from "lucide-react"

function formatPrice(n: number | null) {
  if (n === null) return null
  return n.toLocaleString("es-AR", { style: "currency", currency: "ARS", maximumFractionDigits: 0 })
}

const categoryIcons: Record<string, string> = {
  "Accesorios": "🎒", "Audio": "🔊", "Bicicletas": "🚲", "Celulares": "📱",
  "Cocinas/Hornos/Microondas": "🍳", "Combos": "📦", "Deportes": "⚽", "Gaming": "🎮",
  "Heladeras/Freezers": "❄️", "Herramientas": "🔧", "Hogar/Baño": "🛁",
  "Lavarropas/Secarropas": "🌀", "Outdoor/Playa": "🏖️",
  "Pequeños Electrodomésticos": "🍳", "TVs": "📺", "Tablets": "📱",
}

export default async function CategoriaPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  const categories = await getCategories()
  const category = categories.find((c) => c.slug === slug)
  if (!category) notFound()

  const { products: catProducts } = await getProducts({ category_id: category.id, limit: "1000" })

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <Link href="/categorias" className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700">
            <ArrowLeft className="w-4 h-4" />
            Volver a categorías
          </Link>
          <Link href="/productos" className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700">
            Ir al Catálogo
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="mb-8">
          <span className="text-4xl">{categoryIcons[category.name] || "📦"}</span>
          <h1 className="text-3xl font-bold text-gray-900 mt-2">{category.name}</h1>
          <p className="text-gray-600 mt-1">{catProducts.length} productos</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {catProducts.map((p) => (
            <Link
              key={p.sku}
              href={`/producto/${p.slug}`}
              className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg hover:border-blue-300 transition-all duration-300"
            >
              <div className="h-48 bg-gray-100 overflow-hidden">
                {p.images.length > 0 ? (
                  <img
                    src={p.images[0]}
                    alt={p.name}
                    className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                    loading="lazy"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-5xl">
                    {categoryIcons[p.category] || "📦"}
                  </div>
                )}
              </div>
              <div className="p-4">
                <h3 className="font-semibold text-gray-900 line-clamp-2 text-sm">{p.name}</h3>
                {p.prices.precio_lista && (
                  <p className="text-xs text-gray-400 line-through mt-1">
                    Lista: {formatPrice(p.prices.precio_lista)}
                  </p>
                )}
                {p.prices.precio_efectivo && (
                  <p className="text-lg font-bold text-green-600 mt-1">
                    {formatPrice(p.prices.precio_efectivo)}
                  </p>
                )}
                {p.prices.cuota_valor_3 && (
                  <p className="text-xs text-gray-500 mt-1">
                    3x {formatPrice(p.prices.cuota_valor_3)} sin interés
                  </p>
                )}
                {p.prices.cuota_valor_6 && (
                  <p className="text-xs text-gray-500 mt-1">
                    6x {formatPrice(p.prices.cuota_valor_6)} sin interés
                  </p>
                )}
                {p.prices.cuota_valor_12 && (
                  <p className="text-xs text-gray-500 mt-1">
                    12x {formatPrice(p.prices.cuota_valor_12)} con interés
                  </p>
                )}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
