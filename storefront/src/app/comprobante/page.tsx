"use client"

import { useEffect, useState, Suspense } from "react"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Printer, ArrowLeft, CheckCircle2, Clock } from "lucide-react"
import { Order, formatARS, findOrder, saveOrder } from "@/lib/checkout"
import { getBankData } from "@/lib/banco"

const NEGOCIO = {
  nombre: "DankoShop",
  direccion: "Calle 26 Número 207, La Plata, Buenos Aires",
  telefono: "221 621 9596",
  email: "ventas@dankoshop.com.ar",
}

function ComprobanteInner() {
  const params = useSearchParams()
  const ref = params.get("ref")
  const status = params.get("status")
  const [order, setOrder] = useState<Order | null>(null)
  const [notFound, setNotFound] = useState(false)
  const banco = getBankData()

  useEffect(() => {
    if (!ref) return setNotFound(true)
    let o = findOrder(ref)
    if (o && status === "success" && o.estado !== "pagado") {
      o = { ...o, estado: "pagado" }
      saveOrder(o)
    }
    if (o) setOrder(o)
    else setNotFound(true)
  }, [ref, status])

  if (notFound) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Comprobante no encontrado</h1>
        <p className="text-gray-500 mb-6">No pudimos encontrar tu pedido en este dispositivo.</p>
        <Link href="/productos" className="text-blue-600 hover:underline">Volver a la tienda</Link>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center text-gray-500">
        Cargando comprobante...
      </div>
    )
  }

  const pagado = order.estado === "pagado"

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <Link href="/productos" className="inline-flex items-center text-blue-600 hover:underline text-sm">
          <ArrowLeft className="w-4 h-4 mr-1" /> Volver a la tienda
        </Link>
        <button
          onClick={() => window.print()}
          className="inline-flex items-center bg-gray-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-700"
        >
          <Printer className="w-4 h-4 mr-2" /> Imprimir / Guardar PDF
        </button>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-8">
        {/* Cabecera */}
        <div className="flex items-start justify-between border-b pb-4">
          <div>
            <h1 className="text-2xl font-extrabold text-gray-900">{NEGOCIO.nombre}</h1>
            <p className="text-sm text-gray-500">{NEGOCIO.direccion}</p>
            <p className="text-sm text-gray-500">{NEGOCIO.telefono} · {NEGOCIO.email}</p>
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-gray-400">Comprobante de pedido</p>
            <p className="text-lg font-bold text-gray-900">{order.id}</p>
            <p className="text-xs text-gray-500">{new Date(order.fecha).toLocaleString("es-AR")}</p>
          </div>
        </div>

        {/* Estado */}
        <div
          className={`mt-4 flex items-center gap-2 rounded-lg px-4 py-3 ${
            pagado ? "bg-green-50 text-green-800" : "bg-amber-50 text-amber-800"
          }`}
        >
          {pagado ? <CheckCircle2 className="w-5 h-5" /> : <Clock className="w-5 h-5" />}
          <span className="font-medium">
            {pagado ? "PAGO CONFIRMADO" : "PENDIENTE DE PAGO"}
            {order.pago_ref ? ` · Operación: ${order.pago_ref}` : ""}
          </span>
        </div>

        {/* Cliente */}
        <div className="mt-4 text-sm text-gray-700">
          <p className="font-semibold text-gray-900">Cliente</p>
          <p>{order.cliente.nombre} {order.cliente.dni ? `(DNI/CUIT: ${order.cliente.dni})` : ""}</p>
          <p>Email: {order.cliente.email} · Tel: {order.cliente.telefono}</p>
          <p>
            {order.cliente.metodo_envio === "retiro"
              ? "Retiro en local (Calle 26 N° 207, La Plata)"
              : `Envío a: ${order.cliente.direccion}, ${order.cliente.ciudad}, ${order.cliente.provincia}`}
          </p>
        </div>

        {/* Items */}
        <table className="w-full mt-6 text-sm">
          <thead>
            <tr className="text-left text-gray-400 border-b text-xs uppercase">
              <th className="py-2">Producto</th>
              <th className="py-2 text-right">Cant.</th>
              <th className="py-2 text-right">Precio</th>
              <th className="py-2 text-right">Subtotal</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((it) => (
              <tr key={it.sku} className="border-b border-gray-100">
                <td className="py-2">
                  <span className="text-gray-900">{it.name}</span>
                  <span className="block text-xs text-gray-400">SKU: {it.sku}</span>
                </td>
                <td className="py-2 text-right">{it.quantity}</td>
                <td className="py-2 text-right">{formatARS(it.price)}</td>
                <td className="py-2 text-right font-medium">{formatARS((it.price || 0) * (it.quantity || 1))}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Totales */}
        <div className="mt-4 ml-auto w-64 space-y-1 text-sm">
          <div className="flex justify-between text-gray-600"><span>Subtotal</span><span>{formatARS(order.subtotal)}</span></div>
          <div className="flex justify-between text-gray-600"><span>Envío</span><span>{order.envio === 0 ? "Gratis" : formatARS(order.envio)}</span></div>
          <div className="flex justify-between text-lg font-bold text-gray-900 border-t pt-2"><span>Total</span><span>{formatARS(order.total)}</span></div>
        </div>

        {/* Método de pago */}
        <div className="mt-6 border-t pt-4 text-sm">
          <p className="font-semibold text-gray-900">Método de pago</p>
          <p className="text-gray-700">
            {order.metodo_pago === "mercadopago"
              ? "Mercado Pago (tarjeta / efectivo / cuenta)"
              : `Transferencia bancaria`}
            {order.metodo_pago_label ? ` · ${order.metodo_pago_label}` : ""}
          </p>

          {order.metodo_pago === "transferencia" && !pagado && (
            <div className="mt-3 bg-green-50 border border-green-200 rounded-lg p-3 space-y-1">
              <p className="font-semibold text-green-800">Para acreditar el pago, transferí a:</p>
              <p>Titular: <span className="font-medium">{banco.titular}</span></p>
              <p>Banco: <span className="font-medium">{banco.banco}</span></p>
              <p>Alias CVU: <span className="font-medium break-all">{banco.alias}</span></p>
              <p>CBU: <span className="font-medium break-all">{banco.cbu}</span></p>
              <p>CUIT: <span className="font-medium">{banco.cuit}</span></p>
              <p className="text-xs text-green-700 pt-1">
                Una vez acreditado, confirmamos tu pedido. Mandanos el comprobante de transferencia por
                WhatsApp al {NEGOCIO.telefono} con tu n° de pedido {order.id}.
              </p>
            </div>
          )}
        </div>

        <p className="mt-6 text-center text-xs text-gray-400">
          {NEGOCIO.nombre} · {NEGOCIO.direccion} · Comprobante generado el {new Date(order.fecha).toLocaleString("es-AR")}
        </p>
      </div>

      <style jsx global>{`
        @media print {
          body { background: white; }
          button, a { display: none !important; }
        }
      `}</style>
    </div>
  )
}

export default function ComprobantePage() {
  return (
    <Suspense fallback={<div className="max-w-2xl mx-auto px-4 py-16 text-gray-500">Cargando comprobante...</div>}>
      <ComprobanteInner />
    </Suspense>
  )
}
