import Link from "next/link"
import { Truck, Shield, RotateCcw, Headphones, Facebook, Instagram, Twitter, MapPin, Phone, Mail } from "lucide-react"

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
    { name: "Rastrear pedido", href: "/rastrear" },
    { name: "Métodos de pago", href: "/pagos" },
  ],
  "Mi cuenta": [
    { name: "Mis pedidos", href: "/cuenta/pedidos" },
    { name: "Mis direcciones", href: "/cuenta/direcciones" },
    { name: "Lista de deseos", href: "/cuenta/deseos" },
    { name: "Cerrar sesión", href: "/logout" },
  ],
}

const socialLinks = [
  { name: "Facebook", icon: Facebook, href: "https://facebook.com" },
  { name: "Instagram", icon: Instagram, href: "https://instagram.com" },
  { name: "Twitter", icon: Twitter, href: "https://twitter.com" },
]

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Brand */}
          <div className="lg:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-4">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">D</span>
              </div>
              <span className="text-xl font-bold text-white">DankoShop</span>
            </Link>
            <p className="text-sm text-gray-400 mb-4">
              Tu tienda online de confianza. Productos de tecnología, hogar, outdoor y más con los mejores precios.
            </p>
            <div className="flex gap-4">
              {socialLinks.map((social) => (
                <a key={social.name} href={social.href} target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white transition-colors" aria-label={social.name}>
                  <social.icon className="w-5 h-5" />
                </a>
              ))}
            </div>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([title, links]) => (
            <div key={title}>
              <h3 className="text-white font-semibold mb-4">{title}</h3>
              <ul className="space-y-2">
                {links.map((link) => (
                  <li key={link.name}>
                    <Link href={link.href} className="text-sm text-gray-400 hover:text-white transition-colors">
                      {link.name}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          {/* Contact */}
          <div>
            <h3 className="text-white font-semibold mb-4">Contacto</h3>
            <address className="not-italic space-y-3 text-sm">
              <div className="flex items-start gap-2">
                <MapPin className="w-5 h-5 text-gray-400 mt-0.5 flex-shrink-0" />
                <p>Calle 36 entre 21 y 22, Nro 1328<br />La Plata, Buenos Aires</p>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="w-5 h-5 text-gray-400 flex-shrink-0" />
                <a href="tel:+541167958796" className="hover:text-white transition-colors">11 6795-8796</a>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="w-5 h-5 text-gray-400 flex-shrink-0" />
                <a href="mailto:ventas@dankoshop.com" className="hover:text-white transition-colors">ventas@dankoshop.com</a>
              </div>
            </address>
          </div>
        </div>

        {/* Benefits bar */}
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

        {/* Copyright */}
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