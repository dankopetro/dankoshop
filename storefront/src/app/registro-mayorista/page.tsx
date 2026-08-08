"use client"

import { useState } from "react"
import Link from "next/link"
import { ArrowLeft, Send, CheckCircle2, Loader2 } from "lucide-react"

const input = "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"

export default function RegistroMayoristaPage() {
  const [form, setForm] = useState({ nombre: "", email: "", telefono: "", empresa: "", mensaje: "" })
  const [enviado, setEnviado] = useState(false)
  const [loading, setLoading] = useState(false)

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }))

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    const text = `Hola DankoShop! Quiero ser mayorista:%0A%0A*Nombre:* ${form.nombre}%0A*Email:* ${form.email}%0A*Teléfono:* ${form.telefono}%0A*Empresa:* ${form.empresa || 'No indica'}%0A*Mensaje:* ${form.mensaje || 'Sin mensaje'}`
    window.open(`https://wa.me/5492216219596?text=${text}`, "_blank")
    setEnviado(true)
    setLoading(false)
  }

  if (enviado) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="max-w-md text-center bg-white p-8 rounded-xl border border-gray-200">
          <CheckCircle2 className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">¡Solicitud enviada!</h1>
          <p className="text-gray-600 mb-6">Te contactaremos pronto por WhatsApp para darte los precios mayoristas.</p>
          <Link href="/" className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-medium">
            <ArrowLeft className="w-4 h-4" /> Volver al inicio
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-12">
        <Link href="/" className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-6 text-sm">
          <ArrowLeft className="w-4 h-4" /> Volver al inicio
        </Link>

        <div className="bg-white p-8 rounded-xl border border-gray-200">
          <div className="text-center mb-8">
            <div className="text-4xl mb-3">✨</div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Quiero ser mayorista</h1>
            <p className="text-gray-600">
              Completá tus datos y te contactamos con precios especiales para revendedores.
              Comprá 3 unidades o más del mismo producto y accedé a descuentos exclusivos.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nombre y apellido *</label>
              <input className={input} required value={form.nombre} onChange={(e) => set("nombre", e.target.value)} />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input className={input} type="email" required value={form.email} onChange={(e) => set("email", e.target.value)} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Teléfono / WhatsApp *</label>
                <input className={input} required value={form.telefono} onChange={(e) => set("telefono", e.target.value)} />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nombre de tu empresa o negocio</label>
              <input className={input} value={form.empresa} onChange={(e) => set("empresa", e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mensaje (opcional)</label>
              <textarea className={input + " min-h-[80px]"} value={form.mensaje} onChange={(e) => set("mensaje", e.target.value)} placeholder="Contanos qué productos te interesan..." />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-medium py-3 rounded-lg flex items-center justify-center gap-2 transition-colors"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              Enviar solicitud por WhatsApp
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
