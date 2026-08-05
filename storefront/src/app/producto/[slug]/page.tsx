import { notFound } from "next/navigation"
import Image from "next/image"
import Link from "next/link"
import { format } from "@/lib/utils"
import { ShoppingCart, Truck, Shield, RotateCcw, Banknote, CreditCard, Users, Tag } from "lucide-react"
import { getProduct } from "@/lib/medusa"

export default async function ProductoPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  let product: any = null

  try {
    product = await getProduct(slug)
  } catch {
    notFound()
  }

  if (!product) notFound()

  const precioLista = product.metadata?.precio_lista || product.variants?.[0]?.prices?.[0]?.amount || 0
  const precioEfectivo = product.metadata?.precio_efectivo || Math.round(precioLista * 0.85)
  const precioTransferencia = product.metadata?.precio_transferencia || Math.round(precioLista * 0.90)
  const precioMayorista = product.metadata?.precio_mayorista || Math.round(precioLista * 0.83)
  const cuotas = product.metadata?.cuotas || 3
  const cuotaValor = product.metadata?.cuota_valor || Math.round(precioLista / 3)
  const images = product.images?.length > 0 ? product.images : product.thumbnail ? [{ url: product.thumbnail }] : []

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <nav className="mb-6 text-sm flex items-center gap-2 text-gray-500">
          <Link href="/" className="hover:text-gray-700">Inicio</Link>
          <span>/</span>
          <Link href="/productos" className="hover:text-gray-700">Productos</Link>
          {product.categories?.[0] && (
            <>
              <span>/</span>
              <Link href={`/categoria/${product.categories[0].handle}`} className="hover:text-gray-700">{product.categories[0].name}</Link>
            </>
          )}
          <span>/</span>
          <span className="text-gray-900 font-medium truncate">{product.title}</span>
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Images */}
          <div className="space-y-4">
            <div className="aspect-square overflow-hidden rounded-2xl bg-white border border-gray-200">
              {images[0] ? (
                <Image src={images[0].url} alt={product.title} width={600} height={600} className="w-full h-full object-cover" priority />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-300 text-6xl">📦</div>
              )}
            </div>
            {images.length > 1 && (
              <div className="grid grid-cols-4 gap-3">
                {images.slice(1).map((img: any, idx: number) => (
                  <div key={idx} className="aspect-square overflow-hidden rounded-lg bg-white border border-gray-200">
                    <Image src={img.url} alt={`${product.title} ${idx + 2}`} width={150} height={150} className="w-full h-full object-cover" />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Info */}
          <div className="space-y-6">
            <div>
              {product.categories?.[0] && (
                <span className="inline-block px-3 py-1 text-sm font-medium text-gray-600 bg-gray-100 rounded-full mb-3">
                  {product.categories[0].name}
                </span>
              )}
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{product.title}</h1>
              {product.variants?.[0]?.sku && (
                <p className="text-sm text-gray-500">SKU: {product.variants[0].sku}</p>
              )}
            </div>

            {/* Prices */}
            <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-4">
              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-bold text-gray-900">{format(precioLista)}</span>
              </div>

              <hr className="border-gray-200" />

              <div className="space-y-3">
                {precioEfectivo > 0 && precioEfectivo < precioLista && (
                  <div className="flex items-center gap-3 text-green-700">
                    <Banknote className="w-5 h-5" />
                    <span className="font-medium">Efectivo: {format(precioEfectivo)}</span>
                    <span className="ml-auto text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">15% OFF</span>
                  </div>
                )}
                {precioTransferencia > 0 && precioTransferencia !== precioEfectivo && (
                  <div className="flex items-center gap-3 text-blue-700">
                    <CreditCard className="w-5 h-5" />
                    <span className="font-medium">Transferencia: {format(precioTransferencia)}</span>
                    <span className="ml-auto text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">10% OFF</span>
                  </div>
                )}
                {precioMayorista > 0 && precioMayorista < precioLista && (
                  <div className="flex items-center gap-3 text-purple-700">
                    <Users className="w-5 h-5" />
                    <span className="font-medium">Mayorista (3+): {format(precioMayorista)}</span>
                    <span className="ml-auto text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">17% OFF</span>
                  </div>
                )}
                {cuotas && cuotaValor > 0 && (
                  <div className="flex items-center gap-3 text-gray-700">
                    <Tag className="w-5 h-5" />
                    <span>{cuotas} cuotas sin interés de <strong>{format(cuotaValor)}</strong></span>
                  </div>
                )}
              </div>

              <hr className="border-gray-200" />

              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-600">Cantidad:</span>
                <div className="flex items-center border border-gray-300 rounded-lg">
                  <button className="h-8 w-8 flex items-center justify-center hover:bg-gray-100 rounded-l-lg">-</button>
                  <span className="w-12 text-center font-medium">1</span>
                  <button className="h-8 w-8 flex items-center justify-center hover:bg-gray-100 rounded-r-lg">+</button>
                </div>
              </div>

              <button className="w-full py-3 text-lg font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2">
                <ShoppingCart className="w-5 h-5" />
                Agregar al carrito
              </button>
            </div>

            {/* Benefits */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { icon: Truck, text: "Envío gratis", sub: "+$50.000" },
                { icon: Shield, text: "Garantía", sub: "12 meses" },
                { icon: RotateCcw, text: "Devolución", sub: "30 días" },
              ].map((b) => (
                <div key={b.text} className="text-center p-3 rounded-lg bg-white border border-gray-200">
                  <b.icon className="w-5 h-5 text-blue-600 mx-auto mb-1" />
                  <p className="text-xs font-medium text-gray-900">{b.text}</p>
                  <p className="text-xs text-gray-500">{b.sub}</p>
                </div>
              ))}
            </div>

            {/* Description */}
            {(product.description || product.metadata?.specs) && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Descripción</h3>
                <div className="prose prose-sm text-gray-600 whitespace-pre-line">
                  {product.description || product.metadata?.specs}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}