import { MapPin, Phone, Mail, Clock } from "lucide-react"

export default function ContactoPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Contacto</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm space-y-6">
          <h2 className="text-xl font-semibold text-gray-800">¿Cómo podemos ayudarte?</h2>
          <p className="text-gray-600">Comunícate con nosotros por cualquiera de nuestros canales oficiales o visítanos en nuestro local.</p>
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <MapPin className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
              <div>
                <p className="font-medium text-gray-900">Dirección</p>
                <p className="text-gray-600">Calle 26 Número 207, La Plata, Buenos Aires</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Phone className="w-6 h-6 text-blue-600 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900">WhatsApp / Teléfono</p>
                <a href="https://wa.me/5492216219596" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">221 621 9596</a>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Clock className="w-6 h-6 text-blue-600 flex-shrink-0" />
              <div>
                <p className="font-medium text-gray-900">Horarios de atención</p>
                <p className="text-gray-600">Lunes a Sábados de 9:00 a 19:00 hs</p>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-blue-600 text-white p-8 rounded-xl flex flex-col justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-4">Atención Inmediata por WhatsApp</h2>
            <p className="text-blue-100 mb-6">¿Tenés dudas sobre un producto, envíos o medios de pago? Escribinos ahora y te respondemos al instante.</p>
          </div>
          <a href="https://wa.me/5492216219596?text=Hola%20DankoShop,%20quiero%20hacer%20una%20consulta" target="_blank" rel="noopener noreferrer" className="inline-flex items-center justify-center bg-white text-blue-600 font-semibold px-6 py-3 rounded-lg hover:bg-blue-50 transition-colors">
            Abrir WhatsApp 📲
          </a>
        </div>
      </div>
    </div>
  )
}
