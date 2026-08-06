import { getContent } from "@/content"

interface PagosContent {
  title: string
  intro: string
  items: { label: string; text: string }[]
}

export default function PagosPage() {
  const c = getContent<PagosContent>("pagos")

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">{c.title}</h1>
      <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm space-y-6 text-gray-700 leading-relaxed">
        <p>{c.intro}</p>
        <ul className="list-disc pl-5 space-y-2">
          {c.items.map((item, i) => (
            <li key={i}>
              <strong>{item.label}:</strong> {item.text}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
