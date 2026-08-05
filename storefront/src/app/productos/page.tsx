import { getProducts, getCategories } from "@/lib/medusa"
import { ProductCard } from "@/components/product-card"
import { Button } from "@/components/ui/button"
import { ChevronLeft, ChevronRight, Filter, X } from "lucide-react"
import { useSearchParams } from "next/navigation"
import Link from "next/link"

export default async function ProductosPage({ searchParams }: { searchParams: Promise<{ page?: string; category?: string; q?: string }> }) {
  const params = await searchParams
  const page = parseInt(params.page || "1")
  const category = params.category
  const q = params.q
  const limit = 12

  let productsData: any = { products: [], count: 0 }
  let categories: any[] = []
  
  try {
    [productsData, categories] = await Promise.all([
      getProducts({ limit, offset: (page - 1) * limit, category, q }),
      getCategories()
    ])
  } catch (error) {
    console.error("Error fetching:", error)
  }

  const products = productsData.products || []
  const totalPages = Math.ceil((productsData.count || 0) / limit)

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Catálogo de productos</h1>
          <p className="text-gray-600 mt-1">
            {productsData.count || 0} productos encontrados
            {q && <span className="ml-2 text-blue-600">para "{q}"</span>}
            {category && <span className="ml-2 text-blue-600">en {category}</span>}
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar - Filters */}
          <aside className="lg:w-64 flex-shrink-0">
            <div className="bg-white rounded-lg border border-gray-200 p-6 sticky top-24">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-900">Filtros</h3>
                {(category || q) && (
                  <Button variant="ghost" size="sm" onClick={() => window.location.href = "/productos"}>
                    <X className="w-4 h-4 mr-1" />
                    Limpiar
                  </Button>
                )}
              </div>

              {/* Search */}
              <form action="/productos" method="GET" className="mb-6">
                <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">Buscar</label>
                <div className="relative">
                  <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="search"
                    name="q"
                    id="search"
                    value={q || ""}
                    placeholder="Buscar productos..."
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  />
                </div>
              </form>

              {/* Categories */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Categorías</label>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="category"
                      value=""
                      checked={!category}
                      onChange={() => window.location.href = q ? `/productos?q=${q}` : "/productos"}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-600 hover:text-gray-900">Todas</span>
                  </label>
                  {categories.map((cat: any) => (
                    <label key={cat.id} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="category"
                        value={cat.handle}
                        checked={category === cat.handle}
                        onChange={() => {
                          const base = q ? `/productos?q=${q}&category=${cat.handle}` : `/productos?category=${cat.handle}`
                          window.location.href = base
                        }}
                        className="text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-600 hover:text-gray-900 truncate">{cat.name}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </aside>

          {/* Products Grid */}
          <div className="flex-1 min-w-0">
            {products.length > 0 ? (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
                  {products.map((product: any) => (
                    <ProductCard key={product.id} product={product} />
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-center gap-2">
                    <Button
                      variant="outline"
                      disabled={page === 1}
                      onClick={() => {
                        const url = new URL(window.location.href)
                        url.searchParams.set("page", String(page - 1))
                        window.location.href = url.toString()
                      }}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <span className="px-4 text-sm text-gray-600">
                      Página {page} de {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      disabled={page === totalPages}
                      onClick={() => {
                        const url = new URL(window.location.href)
                        url.searchParams.set("page", String(page + 1))
                        window.location.href = url.toString()
                      }}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-16">
                <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No se encontraron productos</h3>
                <p className="text-gray-500 mb-6">Intenta con otros filtros o términos de búsqueda</p>
                <Button onClick={() => window.location.href = "/productos"}>
                  Ver todo el catálogo
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}