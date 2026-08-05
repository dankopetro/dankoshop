"use client"

import Link from "next/link"
import { ShoppingCart, Menu, X, Search, User } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Separator } from "@/components/ui/separator"

const categories = [
  { name: "Celulares", href: "/categoria/celulares" },
  { name: "TVs", href: "/categoria/tvs" },
  { name: "Lavarropas/Secarropas", href: "/categoria/lavarropas-secarropas" },
  { name: "Heladeras/Freezers", href: "/categoria/heladeras-freezers" },
  { name: "Cocinas/Hornos/Microondas", href: "/categoria/cocinas-hornos-microondas" },
  { name: "Pequeños Electrodomésticos", href: "/categoria/pequenos-electrodomesticos" },
  { name: "Bicicletas", href: "/categoria/bicicletas" },
  { name: "Outdoor/Playa", href: "/categoria/outdoor-playa" },
  { name: "Herramientas", href: "/categoria/herramientas" },
  { name: "Hogar/Baño", href: "/categoria/hogar-bano" },
  { name: "Gaming", href: "/categoria/gaming" },
  { name: "Tablets", href: "/categoria/tablets" },
]

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 w-full bg-white border-b border-gray-200">
      {/* Top bar */}
      <div className="hidden md:flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-200 text-sm text-gray-600">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Envíos a todo el país - La Plata, Calle 36 entre 21 y 22, Nro 1328
          </span>
          <span className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            Pedidos: 11 6795-8796 (CARLA IA 24hs)
          </span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/cuenta" className="hover:text-gray-900 transition-colors">Mi cuenta</Link>
          <Link href="/carrito" className="hover:text-gray-900 transition-colors flex items-center gap-1">
            <ShoppingCart className="w-4 h-4" />
            Carrito
          </Link>
        </div>
      </div>

      {/* Main header */}
      <div className="flex items-center justify-between px-4 py-4 md:px-8">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2" aria-label="DankoShop Home">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">D</span>
          </div>
          <span className="text-xl font-bold text-gray-900">DankoShop</span>
        </Link>

        {/* Search */}
        <div className="hidden md:flex-1 max-w-2xl mx-8">
          <form action="/buscar" className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <Input
              type="search"
              name="q"
              placeholder="Buscar productos..."
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              autoComplete="off"
            />
          </form>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-4">
          <Link href="/carrito" className="relative p-2 text-gray-600 hover:text-gray-900 transition-colors">
            <ShoppingCart className="w-6 h-6" />
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">0</span>
          </Link>
          <Link href="/cuenta" className="p-2 text-gray-600 hover:text-gray-900 transition-colors md:hidden">
            <User className="w-6 h-6" />
          </Link>
          <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="md:hidden">
                <Menu className="w-6 h-6" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-80">
              <div className="flex flex-col gap-4 p-4">
                <h3 className="font-semibold text-lg">Categorías</h3>
                <nav className="flex flex-col gap-2">
                  {categories.map((cat) => (
                    <Link key={cat.name} href={cat.href} className="text-gray-600 hover:text-gray-900 transition-colors px-2 py-2">
                      {cat.name}
                    </Link>
                  ))}
                </nav>
                <Separator />
                <div className="flex flex-col gap-2">
                  <Link href="/cuenta" className="text-gray-600 hover:text-gray-900 px-2 py-2">Mi cuenta</Link>
                  <Link href="/carrito" className="text-gray-600 hover:text-gray-900 px-2 py-2 flex items-center gap-2">
                    <ShoppingCart className="w-5 h-5" />
                    Carrito
                  </Link>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>

      {/* Mobile search */}
      <div className="md:hidden px-4 pb-4">
        <form action="/buscar" className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <Input
            type="search"
            name="q"
            placeholder="Buscar productos..."
            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </form>
      </div>

      {/* Mobile category scroll */}
      <div className="md:hidden overflow-x-auto px-4 pb-4 -mx-4">
        <nav className="flex gap-2 min-w-max px-4">
          {categories.map((cat) => (
            <Link key={cat.name} href={cat.href} className="whitespace-nowrap px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-full transition-colors">
              {cat.name}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  )
}