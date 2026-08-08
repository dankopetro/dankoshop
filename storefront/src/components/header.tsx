"use client"

import Link from "next/link"
import { Menu, X, Search } from "lucide-react"
import { useState } from "react"
import CartIcon from "./cart-icon"

const categories = [
  { name: "Combos", slug: "combos" },
  { name: "Audio", slug: "audio" },
]

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 w-full bg-white border-b border-gray-200">
      <div className="flex items-center justify-between px-4 py-4 md:px-8">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">D</span>
          </div>
          <span className="text-xl font-bold text-gray-900">DankoShop</span>
        </Link>

        <form action="/buscar" className="hidden md:flex-1 max-w-2xl mx-8 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="search"
            name="q"
            placeholder="Buscar productos..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </form>

        <div className="flex items-center gap-4">
          <CartIcon />
          <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="md:hidden p-2 text-gray-600">
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white p-4">
          <form action="/buscar" className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input type="search" name="q" placeholder="Buscar..." className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg" />
          </form>
          <nav className="grid grid-cols-2 gap-2">
            {categories.map((cat) => (
              <Link key={cat.slug} href={`/categoria/${cat.slug}`} className="text-sm text-gray-600 hover:text-gray-900 px-3 py-2 rounded-lg hover:bg-gray-100">
                {cat.name}
              </Link>
            ))}
          </nav>
        </div>
      )}

      <div className="md:hidden overflow-x-auto px-4 pb-3 -mx-4">
        <nav className="flex gap-2 min-w-max px-4">
          {categories.map((cat) => (
            <Link key={cat.slug} href={`/categoria/${cat.slug}`} className="whitespace-nowrap px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full">
              {cat.name}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  )
}