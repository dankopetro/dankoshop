export default function ProductosPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Catálogo de productos</h1>
          <p className="text-gray-600 mt-1">Cargando productos...</p>
        </div>
        <div className="text-center py-16">
          <p className="text-gray-500">Los productos se cargan dinámicamente desde el servidor.</p>
          <p className="text-sm text-gray-400 mt-2">Asegurate de que el backend de Medusa esté corriendo.</p>
        </div>
      </div>
    </div>
  )
}