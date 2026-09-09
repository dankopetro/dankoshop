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
