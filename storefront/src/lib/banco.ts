export interface BankData {
  titular: string
  cbu: string
  alias: string
  cuit: string
  banco: string
}

// Datos bancarios de DankoShop. Defaults locales editables vía env vars.
export function getBankData(): BankData {
  return {
    titular: process.env.NEXT_PUBLIC_BANCO_TITULAR || "",
    cbu: process.env.NEXT_PUBLIC_BANCO_CBU || "",
    alias: process.env.NEXT_PUBLIC_BANCO_ALIAS || "",
    cuit: process.env.NEXT_PUBLIC_BANCO_CUIT || "",
    banco: process.env.NEXT_PUBLIC_BANCO_NOMBRE || "",
  }
}
