export default function FaqPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Preguntas Frecuentes</h1>
      <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm space-y-6">
        <div>
          <h3 className="font-semibold text-lg text-gray-900">¿Cuáles son los medios de pago disponibles?</h3>
          <p className="text-gray-600 mt-1">Aceptamos efectivo en el local, transferencia bancaria con descuento y tarjetas de crédito en cuotas.</p>
        </div>
        <div>
          <h3 className="font-semibold text-lg text-gray-900">¿Cómo hago para comprar?</h3>
          <p className="text-gray-600 mt-1">Agregás los productos al carrito y hacés click en finalizar compra para enviar el pedido directamente por WhatsApp a nuestro asesor.</p>
        </div>
        <div>
          <h3 className="font-semibold text-lg text-gray-900">¿Dónde están ubicados?</h3>
          <p className="text-gray-600 mt-1">Nuestro local está en Calle 26 Número 207, La Plata, Buenos Aires.</p>
        </div>
      </div>
    </div>
  )
}
