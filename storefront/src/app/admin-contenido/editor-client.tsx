"use client"

import { useState } from "react"

interface ContentPage {
  key: string
  label: string
  file: string
  data: unknown
}

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v)
}

function countLeaves(data: unknown): number {
  if (Array.isArray(data)) {
    let n = 0
    for (const item of data as unknown[]) {
      n += isPlainObject(item) ? countLeaves(item) : 1
    }
    return n
  }
  if (isPlainObject(data)) {
    let n = 0
    for (const v of Object.values(data)) {
      n += countLeaves(v)
    }
    return n
  }
  return 1
}

function serialize(data: unknown): string {
  return JSON.stringify(data, null, 2)
}

export default function EditorClient({ pages }: { pages: ContentPage[] }) {
  const [selected, setSelected] = useState<string>(pages[0]?.key || "")
  const [password, setPassword] = useState("")
  const [json, setJson] = useState<string>(() =>
    JSON.stringify(pages[0]?.data ?? {}, null, 2),
  )
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null)

  const page = pages.find((p) => p.key === selected)

  function select(key: string) {
    const p = pages.find((pp) => pp.key === key)
    if (!p) return
    setSelected(key)
    setJson(JSON.stringify(p.data, null, 2))
    setMsg(null)
  }

  async function save() {
    if (!page) return
    setSaving(true)
    setMsg(null)
    let parsed: unknown
    try {
      parsed = JSON.parse(json)
    } catch (e) {
      setMsg({ ok: false, text: `JSON inválido: ${e instanceof Error ? e.message : String(e)}` })
      setSaving(false)
      return
    }
    const res = await fetch("/api/contenido", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password, file: page.file, data: parsed }),
    })
    const result = await res.json()
    if (res.ok && result.ok) {
      setMsg({ ok: true, text: "Contenido guardado. El sitio se actualizará en unos minutos." })
    } else {
      setMsg({ ok: false, text: result.error || "Error al guardar" })
    }
    setSaving(false)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Editor de Contenido</h1>
        <p className="text-gray-600 mb-8">
          Editar las páginas institucionales. Los cambios se publican automáticamente al guardar.
        </p>

        <div className="flex flex-wrap gap-2 mb-8">
          {pages.map((p) => (
            <button
              key={p.key}
              onClick={() => select(p.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selected === p.key
                  ? "bg-blue-600 text-white"
                  : "bg-white border border-gray-300 text-gray-700 hover:border-blue-300"
              }`}
            >
              {p.label} ({countLeaves(p.data)} campos)
            </button>
          ))}
        </div>

        {page && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <div>
                <h2 className="font-semibold text-gray-900">{page.label}</h2>
                <p className="text-xs text-gray-400">{page.file}</p>
              </div>
            </div>
            <div className="p-6">
              <textarea
                value={json}
                onChange={(e) => setJson(e.target.value)}
                spellCheck={false}
                className="w-full h-96 font-mono text-sm border border-gray-300 rounded-lg p-4 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <div className="mt-4 space-y-4">
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Contraseña de administración"
                  className="w-full max-w-xs px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <div className="flex items-center gap-4">
                  <button
                    onClick={save}
                    disabled={saving}
                    className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
                  >
                    {saving ? "Guardando..." : "Guardar cambios"}
                  </button>
                  {msg && (
                    <span className={`text-sm ${msg.ok ? "text-green-600" : "text-red-600"}`}>
                      {msg.text}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-6 text-sm text-gray-700">
          <p className="font-semibold text-blue-800 mb-2">⚠️ Cómo editar el JSON</p>
          <p>Mantené la estructura tal cual está. Podés cambiar los textos entre comillas.</p>
          <ul className="list-disc pl-5 mt-2 space-y-1">
            <li>Los campos <code>title</code>, <code>intro</code>, <code>body</code> aceptan HTML básico (&lt;strong&gt;, &lt;br&gt;).</li>
            <li>Para agregar un ítem nuevo en una lista, copiá un objeto <code>{"{ }"}</code> existente y pegálo antes de la coma de cierre.</li>
            <li>No borres comas, llaves o corchetes o el JSON se romperá.</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
