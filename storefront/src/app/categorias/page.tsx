import { categories } from "@/data/products"
import Link from "next/link"

const categoryIcons: Record<string, string> = {
  "Accesorios": "🎒", "Bicicletas": "🚲", "Celulares": "📱", "Cocinas/Hornos/Microondas": "🍳",
  "Combos": "📦", "Deportes": "⚽", "Gaming": "🎮", "Heladeras/Freezers": "❄️",
  "Herramientas": "🔧", "Hogar/Baño": "🛁", "Lavarropas/Secarropas": "🌀",
  "Outdoor/Playa": "🏖️", "Pequeños Electrodomésticos": "🍳", "TVs": "📺",
  "Tablets": "📱", "Varios": "📦",
}

export default function CategoriasPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Categorías</h1>
          <p className="text-gray-600 mt-1">Explorá todos los productos por categoría</p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-4 gap-4">
          {categories.map((cat) => (
            <Link key={cat.slug} href={`/categoria/${cat.slug}`} className="group">
              <div className="h-full text-center p-6 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-lg transition-all duration-300 cursor-pointer">
                <div className="text-4xl mb-3">{categoryIcons[cat.name] || "📦"}</div>
                <h3 className="font-medium text-gray-900 group-hover:text-blue-600">{cat.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{cat.count} productos</p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
