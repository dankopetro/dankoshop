import { getContent } from "@/content"

interface PrivacidadContent {
  title: string
  paragraphs: string[]
}

export default function PrivacidadPage() {
  const c = getContent<PrivacidadContent>("privacidad")

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">{c.title}</h1>
      <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm space-y-4 text-gray-700">
        {c.paragraphs.map((p, i) => (
          <p key={i}>{p}</p>
        ))}
      </div>
    </div>
  )
}
