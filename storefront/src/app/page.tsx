import { getProducts, getCategories } from "@/lib/medusa"
import { ProductCard } from "@/components/product-card"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { ArrowRight, Sparkles, Truck, Shield, RotateCcw, Headphones } from "lucide-react"

const benefits = [
  { icon: Truck, title: "Envío gratis", desc: "En compras superiores a $50.000" },
  { icon: Shield, title: "Compra 100% segura", desc: "SSL certificado y pagos protegidos" },
  { icon: RotateCcw, title: "Devoluciones fáciles", desc: "30 días para cambiar o devolver" },
  { icon: Headphones, title: "Soporte 24/7", desc: "CARLA nuestra IA te atiende siempre" },
]

const categories = [
  { name: "Celulares", slug: "celulares", icon: "📱" },
  { name: "TVs", slug: "tvs", icon: "📺" },
  { name: "Lavarropas/Secarropas", slug: "lavarropas-secarropas", icon: "🌀" },
  { name: "Heladeras/Freezers", slug: "heladeras-freezers", icon: "❄️" },
  { name: "Cocinas/Hornos", slug: "cocinas-hornos-microondas", icon: "🍳" },
  { name: "Pequeños Electrodomésticos", slug: "pequenos-electrodomesticos", icon: "🍟" },
  { name: "Bicicletas", slug: "bicicletas", icon: "🚲" },
  { name: "Outdoor/Playa", slug: "outdoor-playa", icon: "🏖️" },
  { name: "Herramientas", slug: "herramientas", icon: "🔧" },
  { name: "Hogar/Baño", slug: "hogar-bano", icon: "🛁" },
  { name: "Gaming", slug: "gaming", icon: "🎮" },
  { name: "Tablets", slug: "tablets", icon: "📱" },
]

export default async function Home() {
  let products: any[] = []
  try {
    const response = await getProducts({ limit: 8 })
    products = response.products || []
  } catch (error) {
    console.error("Error fetching products:", error)
  }

  return (
    <div className="flex flex-col flex-1 bg-gray-50">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white overflow-hidden">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
          <div className="max-w-3xl">
            <span className="inline-block px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-sm text-sm font-medium mb-6">
              🚀 Envío gratis en compras +$50.000 • 15% OFF efectivo • 3 cuotas sin interés
            </span>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
              Todo para tu hogar <br />en un solo lugar
            </h1>
            <p className="text-lg sm:text-xl text-blue-100 mb-8 max-w-2xl">
              Tecnología, electrodomésticos, outdoor, herramientas y más. 
              Precios de mayorista para minoristas. Envíos a todo el país.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link href="/productos">
                <Button size="lg" className="w-full sm:w-auto px-8 py-3 text-lg bg-white text-blue-600 hover:bg-blue-50 transition-colors">
                  Ver productos
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link href="/categorias">
                <Button size="lg" variant="outline" className="w-full sm:w-auto px-8 py-3 text-lg border-white text-white hover:bg-white/10 transition-colors">
                  Categorías
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {benefits.map((benefit) => (
              <div key={benefit.title} className="text-center p-6">
                <div className="w-14 h-14 bg-blue-50 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <benefit.icon className="w-7 h-7 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1">{benefit.title}</h3>
                <p className="text-sm text-gray-600">{benefit.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold text-gray-900">Categorías</h2>
              <p className="text-gray-600 mt-1">Encuentra lo que necesitas</p>
            </div>
            <Link href="/categorias">
              <Button variant="ghost" className="gap-2">
                Ver todas <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
            {categories.map((cat) => (
              <Link key={cat.slug} href={`/categoria/${cat.slug}`} className="group">
                <Card className="h-full text-center p-6 hover:border-blue-300 hover:shadow-lg transition-all duration-300 cursor-pointer">
                  <div className="text-4xl mb-3">{cat.icon}</div>
                  <h3 className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors">{cat.name}</h3>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      {products.length > 0 && (
        <section className="py-16 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-3xl font-bold text-gray-900">Productos destacados</h2>
                <p className="text-gray-600 mt-1">Lo más vendido esta semana</p>
              </div>
              <Link href="/productos">
                <Button variant="ghost" className="gap-2">
                  Ver catálogo completo <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          </div>
        </section>
      )}

      {/* CTA Section */}
      <section className="py-16 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="max-w-2xl mx-auto">
            <Sparkles className="w-12 h-12 text-blue-400 mx-auto mb-4" />
            <h2 className="text-3xl font-bold text-white mb-4">¿Eres revendedor?</h2>
            <p className="text-gray-300 mb-8 text-lg">
              Accede a precios de mayorista comprando 3 unidades o más. 
              Registrate y empezá a ganar más con cada venta.
            </p>
            <Link href="/registro-mayorista">
              <Button size="lg" className="px-8 py-3 text-lg bg-blue-600 hover:bg-blue-700 text-white">
                Quiero ser mayorista
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}