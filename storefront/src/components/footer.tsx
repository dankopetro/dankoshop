import Link from "next/link"
import { Truck, Shield, RotateCcw, Headphones, MapPin, Mail } from "lucide-react"

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

function WhatsAppIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="#25D366">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
    </svg>
  )
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
              <div className="flex items-center gap-2">
                <WhatsAppIcon className="w-5 h-5 flex-shrink-0" />
                <a href="https://wa.me/5492216219596" target="_blank" rel="noopener noreferrer" className="hover:text-white">221 621 9596</a>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="w-5 h-5 text-gray-400 flex-shrink-0" />
                <a href="mailto:ventas@dankoshop.com.ar" className="hover:text-white">ventas@dankoshop.com.ar</a>
              </div>
            </address>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-gray-800">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { icon: Truck, title: "Envío gratis", desc: "En compras +$200.000" },
              { icon: Shield, title: "Compra segura", desc: "SSL certificado" },
              { icon: RotateCcw, title: "Devoluciones", desc: "30 días gratis" },
              { icon: Headphones, title: "Soporte 24/7", desc: "Mary IA" },
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
            Desarrollado con Next.js + MedusaJS ·{" "}
            <a href="mailto:admin@dankoshop.com.ar" className="hover:text-gray-300">Admin</a>
          </p>
        </div>
      </div>
    </footer>
  )
}
