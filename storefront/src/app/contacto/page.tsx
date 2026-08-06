import { MapPin, Phone, Clock } from "lucide-react"
import { getContent } from "@/content"

interface ContactoContent {
  title: string
  subtitle: string
  address: string
  phone: string
  whatsapp: string
  whatsappMessage: string
  hours: string
  ctaTitle: string
  ctaText: string
}

export default function ContactoPage() {
  const c = getContent<ContactoContent>("contacto")
  const waLink = `https://wa.me/${c.whatsapp}?text=${encodeURIComponent(c.whatsappMessage)}`

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">{c.title}</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm space-y-6">
          <h2 className="text-xl font-semibold text-gray-800">¿Cómo podemos ayudarte?</h2>
          <p className="text-gray-600">{c.subtitle}</p>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <MapPin className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
              <div>
                <p className="font-medium text-gray-900">Dirección</p>
                <p className="text-gray-600">{c.address}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Phone className="w-6 h-6 text-blue-600 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900">WhatsApp / Teléfono</p>
                <a href={waLink} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{c.phone}</a>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="w-6 h-6 text-blue-600 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900">Horarios de atención</p>
                <p className="text-gray-600">{c.hours}</p>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-blue-600 text-white p-8 rounded-xl flex flex-col justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-4">{c.ctaTitle}</h2>
            <p className="text-blue-100 mb-6">{c.ctaText}</p>
          </div>
          <a href={waLink} target="_blank" rel="noopener noreferrer" className="inline-flex items-center justify-center bg-white text-blue-600 font-semibold px-6 py-3 rounded-lg hover:bg-blue-50 transition-colors">
            Abrir WhatsApp 📲
          </a>
        </div>
      </div>
    </div>
  )
}
