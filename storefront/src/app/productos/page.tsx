export default async function ProductosPage({ searchParams }: { searchParams: Promise<{ page?: string; category?: string; q?: string }> }) {
  const params = await searchParams
  const page = parseInt(params.page || "1")
  const category = params.category
  const q = params.q
  const limit = 12

  // Client-side fetch - no data at build time
  let products: any[] = []
  try {
    const medusaUrl = process.env.NEXT_PUBLIC_MEDUSA_BACKEND_URL || "http://localhost:9000"
    const res = await fetch(`${medusaUrl}/store/products?limit=${limit}&offset=${(page - 1) * limit}`, { cache: "no-store" })
    if (res.ok) {
      const data = await res.json()
      products = data.products || []
    }
  } catch (error) {
    console.error("Error fetching products:", error)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Catálogo de productos</h1>
          <p className="text-gray-600 mt-1">
            {products.length} productos encontrados
            {q && <span className="ml-2 text-blue-600">para "{q}"</span>}
          </p>
        </div>

        {products.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((product: any) => (
              <a key={product.id} href={`/producto/${product.handle}`} className="group">
                <div className="h-full bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-lg transition-all overflow-hidden">
                  <div className="aspect-square bg-gray-50 relative overflow-hidden">
                    {product.thumbnail && (
                      <img src={product.thumbnail} alt={product.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                    )}
                  </div>
                  <div className="p-4">
                    <h3 className="font-medium text-gray-900 line-clamp-2 mb-2">{product.title}</h3>
                    {product.variants?.[0]?.prices?.[0] && (
                      <div className="text-lg font-bold text-gray-900">
                        ${product.variants[0].prices[0].amount.toLocaleString("es-AR")}
                      </div>
                    )}
                  </div>
                </div>
              </a>
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <p className="text-gray-500 mb-4">No se encontraron productos</p>
            <p className="text-sm text-gray-400">Asegurate de que el backend de Medusa esté corriendo y tengas productos importados.</p>
          </div>
        )}
      </div>
    </div>
  )
}