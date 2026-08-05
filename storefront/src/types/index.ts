export interface Product {
  id: string
  title: string
  handle: string
  subtitle?: string
  description?: string
  thumbnail?: string
  images: Array<{ id: string; url: string }>
  variants: Array<{
    id: string
    title: string
    sku: string
    prices: Array<{ amount: number; currency_code: string }>
    options: Array<{ value: string }>
  }>
  options: Array<{ id: string; title: string; values: string[] }>
  categories: Array<{ id: string; name: string; handle: string }>
  metadata?: {
    precio_lista?: number
    precio_efectivo?: number
    precio_transferencia?: number
    precio_mayorista?: number
    precio_mayorista_transferencia?: number
    cuotas?: number
    cuota_valor?: number
  }
}

export interface Category {
  id: string
  name: string
  handle: string
  parent_category_id?: string
  category_children?: Category[]
}