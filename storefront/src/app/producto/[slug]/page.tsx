import { getProduct, getProducts } from "@/lib/medusa"
import { notFound } from "next/navigation"
import Image from "next/image"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { format } from "@/lib/utils"
import { ShoppingCart, Truck, Shield, RotateCcw, Banknote, CreditCard, Users, Tag, Check } from "lucide-react"
import Link from "next/link"
import AddToCartButton from "@/components/add-to-cart-button"

export async function generateStaticParams() {
  try {
    const { products } = await getProducts({ limit: 100 })
    return products.map((product: any) => ({
      slug: product.handle,
    }))
  } catch {
    return []
  }
}

export default async function ProductoPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params
  let product: any

  try {
    product = await getProduct(slug)
  } catch {
    notFound()
  }

  const precioLista = product.metadata?.precio_lista || product.variants[0]?.prices[0]?.amount || 0
  const precioEfectivo = product.metadata?.precio_efectivo || Math.round(precioLista * 0.85)
  const precioTransferencia = product.metadata?.precio_transferencia || Math.round(precioLista * 0.90)
  const precioMayorista = product.metadata?.precio_mayorista || Math.round(precioLista * 0.83)
  const cuotas = product.metadata?.cuotas || 3
  const cuotaValor = product.metadata?.cuota_valor || Math.round(precioLista / 3)
  const images = product.images?.length > 0 ? product.images : product.thumbnail ? [{ url: product.thumbnail }] : []

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Breadcrumb */}
        <nav className="mb-6 text-sm">
          <ol className="flex items-center gap-2 text-gray-500">
            <li><Link href="/" className="hover:text-gray-700">Inicio</Link></li>
            <li><ChevronIcon /></li>
            <li><Link href="/productos" className="hover:text-gray-700">Productos</Link></li>
            {product.categories?.[0] && (
              <>
                <li><ChevronIcon /></li>
                <li><Link href={`/categoria/${product.categories[0].handle}`} className="hover:text-gray-700">{product.categories[0].name}</Link></li>
              </>
            )}
            <li><ChevronIcon /></li>
            <li className="text-gray-900 font-medium truncate">{product.title}</li>
          </ol>
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Images */}
          <div className="space-y-4">
            <div className="aspect-square overflow-hidden rounded-2xl bg-white border border-gray-200">
              {images[0] ? (
                <Image
                  src={images[0].url}
                  alt={product.title}
                  width={600}
                  height={600}
                  className="w-full h-full object-cover"
                  priority
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-300">
                  <svg className="w-24 h-24" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
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
                <Badge variant="outline" className="mb-3">{product.categories[0].name}</Badge>
              )}
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{product.title}</h1>
              {product.variants?.[0]?.sku && (
                <p className="text-sm text-gray-500">SKU: {product.variants[0].sku}</p>
              )}
            </div>

            {/* Prices */}
            <Card className="p-6 space-y-4">
              <div className="flex items-baseline gap-3">
                <span className="text-3xl font-bold text-gray-900">${format(precioLista)}</span>
                {precioEfectivo < precioLista && (
                  <span className="text-lg text-gray-400 line-through">${format(precioEfectivo)}</span>
                )}
              </div>

              <Separator />

              <div className="space-y-3">
                {precioEfectivo && precioEfectivo < precioLista && (
                  <div className="flex items-center gap-3 text-green-700">
                    <Banknote className="w-5 h-5" />
                    <span className="font-medium">Efectivo: ${format(precioEfectivo)}</span>
                    <Badge className="bg-green-600 text-white text-xs">15% OFF</Badge>
                  </div>
                )}
                {precioTransferencia && precioTransferencia !== precioEfectivo && (
                  <div className="flex items-center gap-3 text-blue-700">
                    <CreditCard className="w-5 h-5" />
                    <span className="font-medium">Transferencia: ${format(precioTransferencia)}</span>
                    <Badge className="bg-blue-600 text-white text-xs">10% OFF</Badge>
                  </div>
                )}
                {precioMayorista && precioMayorista < precioLista && (
                  <div className="flex items-center gap-3 text-purple-700">
                    <Users className="w-5 h-5" />
                    <span className="font-medium">Mayorista (3+ unidades): ${format(precioMayorista)}</span>
                    <Badge className="bg-purple-600 text-white text-xs">17% OFF</Badge>
                  </div>
                )}
                {cuotas && cuotaValor && (
                  <div className="flex items-center gap-3 text-gray-700">
                    <Tag className="w-5 h-5" />
                    <span>{cuotas} cuotas sin interés de <strong>${format(cuotaValor)}</strong></span>
                  </div>
                )}
              </div>

              <Separator />

              <AddToCartButton product={product} />
            </Card>

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

            {/* Specs from metadata */}
            {product.metadata?.specs && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-3">Especificaciones</h3>
                <ul className="space-y-2">
                  {product.metadata.specs.split("\n").filter((s: string) => s.trim()).map((spec: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                      <Check className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                      <span>{spec.replace(/^[✅✔️]\s*/, '')}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function ChevronIcon() {
  return <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
}