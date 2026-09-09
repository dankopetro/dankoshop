import { EnvioZona, EnvioVelocidad } from "./envios"

export interface CartItem {
  sku: string
  name: string
  price: number
  price_lista?: number
  quantity: number
  image?: string
  envio_grande?: boolean
}

export interface Customer {
  nombre: string
  email: string
  telefono: string
  dni: string
  direccion: string
  ciudad: string
  provincia: string
  metodo_envio: "retiro" | "envio"
  zona_envio?: EnvioZona
  velocidad_envio?: EnvioVelocidad
}

export interface Order {
  id: string
  fecha: string
  cliente: Customer
  items: CartItem[]
  subtotal: number
  envio: number
  total: number
  metodo_pago: "mercadopago" | "transferencia"
  estado: "pendiente" | "pagado" | "fallido"
  pago_ref?: string
  metodo_pago_label?: string
}

export const CART_KEY = "dankoshop_cart"
export const ORDERS_KEY = "dankoshop_orders"

export function formatARS(n: number): string {
  return "$" + Math.round(n).toLocaleString("es-AR")
}

export function getCart(): CartItem[] {
  try {
    const raw = localStorage.getItem(CART_KEY)
    return raw ? (JSON.parse(raw) as CartItem[]) : []
  } catch {
    return []
  }
}

export function saveCart(items: CartItem[]) {
  localStorage.setItem(CART_KEY, JSON.stringify(items))
}

export function clearCart() {
  localStorage.removeItem(CART_KEY)
}

export function cartSubtotal(items: CartItem[]): number {
  return items.reduce((acc, it) => acc + (it.price || 0) * (it.quantity || 1), 0)
}

export function calcEnvio(subtotal: number, metodo: Customer["metodo_envio"]): number {
  if (metodo === "retiro") return 0
  const fee = Number(process.env.NEXT_PUBLIC_ENVIO_FEE || 0)
  if (subtotal >= 200000) return 0
  if (subtotal >= 100000) return Math.round(fee * 0.5)
  return fee
}

export function createOrderId(): string {
  return "DK-" + Date.now().toString(36).toUpperCase()
}

export function saveOrder(order: Order) {
  const all = getOrders()
  const idx = all.findIndex((o) => o.id === order.id)
  if (idx >= 0) all[idx] = order
  else all.push(order)
  localStorage.setItem(ORDERS_KEY, JSON.stringify(all))
}

export function getOrders(): Order[] {
  try {
    const raw = localStorage.getItem(ORDERS_KEY)
    return raw ? (JSON.parse(raw) as Order[]) : []
  } catch {
    return []
  }
}

export function findOrder(id: string): Order | undefined {
  return getOrders().find((o) => o.id === id)
}

export function buildOrder(
  cliente: Customer,
  items: CartItem[],
  metodo_pago: Order["metodo_pago"],
  estado: Order["estado"],
  pago_ref?: string,
): Order {
  const subtotal = cartSubtotal(items)
  const envio = calcEnvio(subtotal, cliente.metodo_envio)
  return {
    id: createOrderId(),
    fecha: new Date().toISOString(),
    cliente,
    items,
    subtotal,
    envio,
    total: subtotal + envio,
    metodo_pago,
    estado,
    pago_ref,
  }
}
