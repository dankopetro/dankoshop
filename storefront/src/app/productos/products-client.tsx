"use client"

import { useState } from "react"
import Link from "next/link"
import { Search } from "lucide-react"
import { Product, Category } from "@/lib/medusa"

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

export default function ProductsClient({ products, categories }: { products: Product[]; categories: Category[] }) {
  const [search, setSearch] = useState("")
  const [selectedCat, setSelectedCat] = useState("")

  const filtered = products.filter((p) => {
    const matchSearch = !search || p.name.toLowerCase().includes(search.toLowerCase()) || p.sku.includes(search)
    const matchCat = !selectedCat || p.category === selectedCat
    return matchSearch && matchCat
  })

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Catálogo de productos</h1>
          <p className="text-gray-600 mt-1">{products.length} productos disponibles</p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar por nombre o SKU..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={selectedCat}
            onChange={(e) => setSelectedCat(e.target.value)}
            className="px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 bg-white"
          >
            <option value="">Todas las categorías</option>
            {categories.map((c) => (
              <option key={c.slug} value={c.name}>{c.name} ({c.count})</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filtered.map((p) => (
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
                <span className="text-xs text-blue-600 font-medium">{p.category}</span>
                <h3 className="font-semibold text-gray-900 mt-1 line-clamp-2 text-sm">{p.name}</h3>
                {p.prices.precio_efectivo && (
                  <div className="mt-2">
                    <p className="text-[10px] text-green-600 font-semibold uppercase tracking-wide">Efectivo / Transferencia</p>
                    <p className="text-lg font-bold text-green-600">
                      {formatPrice(p.prices.precio_efectivo)}
                    </p>
                  </div>
                )}
                {p.prices.precio_lista && (
                  <p className="text-xs text-gray-500 mt-1">
                    Lista: <span className="font-medium text-gray-700">{formatPrice(p.prices.precio_lista)}</span> (hasta 12 cuotas)
                  </p>
                )}
              </div>
            </Link>
          ))}
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-16">
            <p className="text-gray-500 text-lg">No se encontraron productos</p>
            <p className="text-sm text-gray-400 mt-1">Intenta con otros filtros</p>
          </div>
        )}
      </div>
    </div>
  )
}
