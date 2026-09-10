export type EnvioZona = "laplata" | "caba-gba" | "prov-ba" | "resto-pais"
export type EnvioVelocidad = "estandar" | "express"

export interface TarifaEnvio {
  zona: EnvioZona
  label: string
  estandar: number
  express: number
}

export const ZONAS_ENVIO: TarifaEnvio[] = [
  { zona: "laplata", label: "La Plata", estandar: 3000, express: 5000 },
  { zona: "caba-gba", label: "CABA / Gran Buenos Aires", estandar: 4000, express: 7000 },
  { zona: "prov-ba", label: "Resto de Provincia Buenos Aires", estandar: 5500, express: 9000 },
  { zona: "resto-pais", label: "Resto del país", estandar: 7000, express: 12000 },
]

export const ENVIO_GRATIS_DESDE = 200000
export const ENVIO_SUBSIDIO_DESDE = 100000
export const ENVIO_SUBSIDIO_PORCENTAJE = 0.5
export const ENVIO_GRATIS_MAX_ABSORBIDO = 10000

// ===================================================================
// FUTURO: Integración con couriers (activar cuando tengas monotributo)
// ===================================================================
// Requiere: CUIT, Cuenta en MiCorreo/Andreani, API keys
//
// export const MICORREO_API_URL = "https://api.correoargentino.com.ar/micorreofr/api/v1"
// export const MICORREO_API_KEY = process.env.MICORREO_API_KEY || ""
// export const MICORREO_CUIT = process.env.MICORREO_CUIT || ""
//
// export const ANDREANI_API_URL = "https://api.andreani.com/v1"
// export const ANDREANI_API_KEY = process.env.ANDREANI_API_KEY || ""
//
// export async function cotizarEnvioCA(
//   peso: number,
//   cp_destino: string,
//   tipo: "sucursal" | "domicilio"
// ): Promise<number> {
//   const response = await fetch(`${MICORREO_API_URL}/cotizar`, {
//     method: "POST",
//     headers: {
//       "Content-Type": "application/json",
//       "Authorization": `Bearer ${MICORREO_API_KEY}`,
//     },
//     body: JSON.stringify({
//       peso,
//       cp_destino,
//       tipo,
//     }),
//   })
//   const data = await response.json()
//   return data.costo
// }
//
// export async function cotizarEnvioAndreani(
//   peso: number,
//   cp_destino: string,
// ): Promise<number> {
//   const response = await fetch(`${ANDREANI_API_URL}/cotizar`, {
//     method: "POST",
//     headers: {
//       "Content-Type": "application/json",
//       "x-api-key": ANDREANI_API_KEY,
//     },
//     body: JSON.stringify({
//       peso,
//       cp_destino,
//     }),
//   })
//   const data = await response.json()
//   return data.costo
// }
// ===================================================================

export function calcEnvioCosto(
  subtotal: number,
  zona: EnvioZona | null,
  velocidad: EnvioVelocidad
): number {
  if (!zona) return 0
  const tarifa = ZONAS_ENVIO.find((z) => z.zona === zona)
  if (!tarifa) return 0
  const costoBase = tarifa[velocidad]

  if (subtotal >= ENVIO_GRATIS_DESDE) return 0
  if (subtotal >= ENVIO_SUBSIDIO_DESDE) {
    return Math.round(costoBase * ENVIO_SUBSIDIO_PORCENTAJE)
  }
  return costoBase
}

export function getEnvioLabel(subtotal: number): string {
  if (subtotal >= ENVIO_GRATIS_DESDE) return "Envío gratis"
  if (subtotal >= ENVIO_SUBSIDIO_DESDE) return "50% OFF en envío"
  return "Envío estándar"
}
