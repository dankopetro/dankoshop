import nosotros from "./nosotros.json"
import envios from "./envios.json"
import faq from "./faq.json"
import pagos from "./pagos.json"
import terminos from "./terminos.json"
import privacidad from "./privacidad.json"
import contacto from "./contacto.json"

export interface ContentPage {
  key: string
  label: string
  file: string
  data: unknown
}

export const contentPages: ContentPage[] = [
  { key: "nosotros", label: "Sobre Nosotros", file: "nosotros.json", data: nosotros },
  { key: "envios", label: "Envíos y Devoluciones", file: "envios.json", data: envios },
  { key: "faq", label: "Preguntas Frecuentes", file: "faq.json", data: faq },
  { key: "pagos", label: "Métodos de Pago", file: "pagos.json", data: pagos },
  { key: "terminos", label: "Términos y Condiciones", file: "terminos.json", data: terminos },
  { key: "privacidad", label: "Política de Privacidad", file: "privacidad.json", data: privacidad },
  { key: "contacto", label: "Contacto", file: "contacto.json", data: contacto },
]

export type PageKey = "nosotros" | "envios" | "faq" | "pagos" | "terminos" | "privacidad" | "contacto"

export function getContent<T = unknown>(key: PageKey): T {
  return (contentPages.find((c) => c.key === key)?.data ?? {}) as T
}
