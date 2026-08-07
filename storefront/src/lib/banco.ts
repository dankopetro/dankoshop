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
    titular: process.env.NEXT_PUBLIC_BANCO_TITULAR || "DANKOSHOP S.R.L.",
    cbu: process.env.NEXT_PUBLIC_BANCO_CBU || "00000031000000000000",
    alias: process.env.NEXT_PUBLIC_BANCO_ALIAS || "danko.shop.cbu",
    cuit: process.env.NEXT_PUBLIC_BANCO_CUIT || "30-00000000-0",
    banco: process.env.NEXT_PUBLIC_BANCO_NOMBRE || "Banco (a confirmar)",
  }
}
