import { getContent } from "@/content"

interface FaqContent {
  title: string
  items: { question: string; answer: string }[]
}

export default function FaqPage() {
  const c = getContent<FaqContent>("faq")

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">{c.title}</h1>
      <div className="bg-white p-8 rounded-xl border border-gray-200 shadow-sm space-y-6">
        {c.items.map((item, i) => (
          <div key={i}>
            <h3 className="font-semibold text-lg text-gray-900">{item.question}</h3>
            <p className="text-gray-600 mt-1">{item.answer}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
