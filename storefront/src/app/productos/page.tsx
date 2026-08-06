import { getProducts, getCategories } from "@/lib/medusa"
import ProductsClient from "./products-client"

export default async function ProductosPage() {
  const [{ products }, categories] = await Promise.all([
    getProducts({ limit: "1000" }),
    getCategories(),
  ])

  return <ProductsClient products={products} categories={categories} />
}
