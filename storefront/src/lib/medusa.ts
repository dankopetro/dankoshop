import { createMedusaClient, MedusaClient } from "@medusajs/medusa-js"

const MEDUSA_BACKEND_URL = process.env.NEXT_PUBLIC_MEDUSA_BACKEND_URL || "http://localhost:9000"
const PUBLISHABLE_API_KEY = process.env.NEXT_PUBLIC_MEDUSA_PUBLISHABLE_KEY

export const medusaClient: MedusaClient = createMedusaClient({
  baseUrl: MEDUSA_BACKEND_URL,
  publishableApiKey: PUBLISHABLE_API_KEY,
  maxRetries: 3,
})

// Helper functions
export async function getProducts(params?: {
  limit?: number
  offset?: number
  category?: string
  q?: string
}) {
  return medusaClient.products.list(params)
}

export async function getProduct(handle: string) {
  return medusaClient.products.retrieve(handle)
}

export async function getCategories() {
  return medusaClient.productCategories.list()
}

export async function getProductById(id: string) {
  return medusaClient.products.retrieve(id)
}