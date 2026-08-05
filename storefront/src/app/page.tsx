import Link from "next/link"
import { ArrowRight, Truck, Shield, RotateCcw, Headphones } from "lucide-react"

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

export default function Home() {
  return (
    <div className="flex flex-col flex-1 bg-gray-50">
      <section className="relative bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white overflow-hidden">
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
              <Link href="/productos" className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium bg-white text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                Ver productos
                <ArrowRight className="w-5 h-5 ml-2" />
              </Link>
              <Link href="/categorias" className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium border border-white text-white hover:bg-white/10 rounded-lg transition-colors">
                Categorías
              </Link>
            </div>
          </div>
        </div>
      </section>

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

      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold text-gray-900">Categorías</h2>
              <p className="text-gray-600 mt-1">Encuentra lo que necesitas</p>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
            {categories.map((cat) => (
              <Link key={cat.slug} href={`/categoria/${cat.slug}`} className="group">
                <div className="h-full text-center p-6 bg-white border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-lg transition-all duration-300 cursor-pointer">
                  <div className="text-4xl mb-3">{cat.icon}</div>
                  <h3 className="font-medium text-gray-900 group-hover:text-blue-600">{cat.name}</h3>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="max-w-2xl mx-auto">
            <div className="text-4xl mb-4">✨</div>
            <h2 className="text-3xl font-bold text-white mb-4">¿Eres revendedor?</h2>
            <p className="text-gray-300 mb-8 text-lg">
              Accede a precios de mayorista comprando 3 unidades o más. 
              Registrate y empezá a ganar más con cada venta.
            </p>
            <Link href="/registro-mayorista" className="inline-flex items-center justify-center px-8 py-3 text-lg font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
              Quiero ser mayorista
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}