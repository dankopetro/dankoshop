import Link from "next/link"
import { Truck, Shield, RotateCcw, Headphones, MapPin, Phone, Mail } from "lucide-react"

const footerLinks = {
  "Información": [
    { name: "Sobre nosotros", href: "/nosotros" },
    { name: "Términos y condiciones", href: "/terminos" },
    { name: "Política de privacidad", href: "/privacidad" },
    { name: "Envíos y devoluciones", href: "/envios" },
  ],
  "Atención al cliente": [
    { name: "Contacto", href: "/contacto" },
    { name: "Preguntas frecuentes", href: "/faq" },
    { name: "Métodos de pago", href: "/pagos" },
  ],
}

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          <div>
            <Link href="/" className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">D</span>
              </div>
              <span className="text-xl font-bold text-white">DankoShop</span>
            </Link>
            <p className="text-sm text-gray-400 mb-4">
              Tu tienda online de confianza. Tecnología, hogar, outdoor y más con los mejores precios.
            </p>
          </div>

          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <h3 className="text-white font-semibold mb-4">{title}</h3>
              <ul className="space-y-2">
                {links.map((link) => (
                  <li key={link.name}>
                    <Link href={link.href} className="text-sm text-gray-400 hover:text-white">
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          <div>
            <h3 className="text-white font-semibold mb-4">Contacto</h3>
            <address className="not-italic space-y-3 text-sm">
              <div className="flex items-start gap-2">
                <MapPin className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
                <p>Calle 36 entre 21 y 22, Nro 1328<br />La Plata, Buenos Aires</p>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="w-5 h-5 text-gray-400 flex-shrink-0" />
                <a href="tel:+541167958796" className="hover:text-white">11 6795-8796</a>
              </div>
            </address>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-gray-800">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { icon: Truck, title: "Envío gratis", desc: "En compras +$50.000" },
              { icon: Shield, title: "Compra segura", desc: "SSL certificado" },
              { icon: RotateCcw, title: "Devoluciones", desc: "30 días gratis" },
              { icon: Headphones, title: "Soporte 24/7", desc: "CARLA IA" },
            ].map((benefit) => (
              <div key={benefit.title} className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-800 rounded-lg flex items-center justify-center">
                  <benefit.icon className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <p className="font-medium text-white text-sm">{benefit.title}</p>
                  <p className="text-gray-400 text-xs">{benefit.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-800 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-gray-400">
            © {new Date().getFullYear()} DankoShop. Todos los derechos reservados.
          </p>
          <p className="text-sm text-gray-500">
            Desarrollado con Next.js + MedusaJS
          </p>
        </div>
      </div>
    </footer>
  )
}