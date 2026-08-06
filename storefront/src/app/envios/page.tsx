import { getContent } from "@/content"

interface EnviosContent {
  title: string
  sections: { heading: string; body: string }[]
}

export default function EnviosPage() {
  const c = getContent<EnviosContent>("envios")

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">{c.title}</h1>
      <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm space-y-6 text-gray-700 leading-relaxed">
        {c.sections.map((s, i) => (
          <div key={i}>
            <h2 className="text-xl font-semibold text-gray-900">{s.heading}</h2>
            <p dangerouslySetInnerHTML={{ __html: s.body }} />
          </div>
        ))}
      </div>
    </div>
  )
}
