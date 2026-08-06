import { getProducts } from "@/lib/medusa"
import ProductCard from "@/components/product-card"

export default async function BuscarPage({ searchParams }: { searchParams: Promise<{ q?: string }> }) {
  const { q } = await searchParams
  const { products: results } = await getProducts({ q: q || "", limit: "100" })

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Resultados de búsqueda: &quot;{q}&quot;</h1>
      {results.length === 0 ? (
        <p className="text-gray-600">No se encontraron productos para tu búsqueda.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {results.map(product => (
            <ProductCard key={product.sku} product={product} />
          ))}
        </div>
      )}
    </div>
  )
}
