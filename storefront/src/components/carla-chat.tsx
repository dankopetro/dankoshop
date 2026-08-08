"use client"

import { useState, useRef, useEffect } from "react"
import { MessageCircle, X, Send, Sparkles } from "lucide-react"

interface ChatMsg {
  from: "user" | "carla"
  text: string
}

const QUICK = ["Medios de pago", "Envíos", "Garantías", "Precios mayoristas"]

export default function CarlaChat() {
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState<ChatMsg[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [msgs, loading, open])

  const send = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || loading) return
    setMsgs((m) => [...m, { from: "user", text: trimmed }])
    setInput("")
    setLoading(true)
    try {
      const res = await fetch("/api/carla", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: trimmed }),
      })
      const data = await res.json()
      setMsgs((m) => [...m, { from: "carla", text: data.reply || "Ups, no pude procesar tu consulta." }])
    } catch {
      setMsgs((m) => [...m, { from: "carla", text: "Hubo un problema de conexión. Intentalo de nuevo 😊" }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {/* Botón flotante */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-5 right-5 z-50 w-14 h-14 rounded-full flex items-center justify-center shadow-lg hover:scale-105 transition-transform"
        style={{ backgroundColor: "#e5ad68" }}
        aria-label="Abrir chat con CARLA"
      >
        {open ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <MessageCircle className="w-6 h-6 text-white" />
        )}
        {!open && (
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
        )}
      </button>

      {/* Ventana de chat */}
      {open && (
        <div className="fixed bottom-24 right-5 z-50 w-[92vw] max-w-sm bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden">
          <div className="px-4 py-3 flex items-center gap-3" style={{ backgroundColor: "#e5ad68" }}>
            <div className="w-9 h-9 rounded-full bg-white/25 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-white font-semibold text-sm">CARLA</p>
              <p className="text-white/80 text-xs">Asistente virtual · Online</p>
            </div>
          </div>

          <div className="flex-1 p-4 space-y-3 overflow-y-auto bg-gray-50 h-72">
            {msgs.length === 0 && (
              <div className="space-y-3">
                <div className="bg-white rounded-2xl rounded-tl-sm p-3 text-sm text-gray-700 shadow-sm">
                  ¡Hola! Soy CARLA 😊, la asistente virtual de DankoShop. Consultame sobre precios, cuotas, envíos, garantías o pagos.
                </div>
                <div className="flex flex-wrap gap-2">
                  {QUICK.map((q) => (
                    <button
                      key={q}
                      onClick={() => send(q)}
                      className="bg-white border border-gray-200 rounded-full px-3 py-1.5 text-xs text-gray-600 hover:border-[#e5ad68] hover:text-[#c98a3d] transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {msgs.map((m, i) => (
              <div key={i} className={`flex ${m.from === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm whitespace-pre-line ${
                    m.from === "user"
                      ? "bg-[#e5ad68] text-white rounded-br-sm"
                      : "bg-white text-gray-700 shadow-sm rounded-bl-sm"
                  }`}
                >
                  {m.text}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-white rounded-2xl rounded-bl-sm px-3 py-2 shadow-sm flex gap-1">
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"></span>
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0.15s]"></span>
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0.3s]"></span>
                </div>
              </div>
            )}

            {msgs.length > 0 && !loading && (
              <div className="flex justify-center pt-1">
                <button
                  onClick={() => setMsgs([])}
                  className="text-xs text-gray-500 hover:text-[#c98a3d] underline underline-offset-2 transition-colors"
                >
                  ↩ Volver al menú principal
                </button>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="p-3 border-t border-gray-200 flex items-center gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send(input)}
              placeholder="Escribí tu consulta..."
              className="flex-1 border border-gray-300 rounded-full px-4 py-2 text-sm focus:ring-2 focus:ring-[#e5ad68] focus:border-transparent outline-none"
            />
            <button
              onClick={() => send(input)}
              className="w-10 h-10 rounded-full flex items-center justify-center hover:scale-105 transition-transform"
              style={{ backgroundColor: "#e5ad68" }}
              aria-label="Enviar"
            >
              <Send className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>
      )}
    </>
  )
}
