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

export const ENVIO_GRATIS_DESDE = 50000

export function calcEnvioCosto(
  subtotal: number,
  zona: EnvioZona | null,
  velocidad: EnvioVelocidad
): number {
  if (!zona) return 0
  if (subtotal >= ENVIO_GRATIS_DESDE) return 0
  const tarifa = ZONAS_ENVIO.find((z) => z.zona === zona)
  if (!tarifa) return 0
  return tarifa[velocidad]
}
