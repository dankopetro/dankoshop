export default function PagosPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Métodos de Pago</h1>
      <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm space-y-6 text-gray-700 leading-relaxed">
        <p>En DankoShop te ofrecemos múltiples opciones para que elijas la que te resulte más cómoda:</p>
        <ul className="list-disc pl-5 space-y-2">
          <li><strong>Efectivo:</strong> Abonando en nuestro local de La Plata.</li>
          <li><strong>Transferencia Bancaria:</strong> Con descuentos especiales.</li>
          <li><strong>Tarjetas de Crédito:</strong> Financiación en cuotas sin interés según promoción vigente.</li>
        </ul>
      </div>
    </div>
  )
}
