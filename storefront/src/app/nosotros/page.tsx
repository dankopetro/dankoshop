import { getContent } from "@/content"

interface NosotrosContent {
  title: string
  intro: string
  paragraphs: string[]
  sectionTitle: string
  sectionBody: string
}

export default function NosotrosPage() {
  const c = getContent<NosotrosContent>("nosotros")

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">{c.title}</h1>
      <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm space-y-6 text-gray-700 leading-relaxed">
        <p className="text-lg" dangerouslySetInnerHTML={{ __html: c.intro }} />
        {c.paragraphs.map((p, i) => (
          <p key={i}>{p}</p>
        ))}
        <h2 className="text-xl font-semibold text-gray-900 pt-4">{c.sectionTitle}</h2>
        <p dangerouslySetInnerHTML={{ __html: c.sectionBody }} />
      </div>
    </div>
  )
}
