// seed-products.js - Run inside Medusa container to seed products
// This script runs inside the Medusa container where it has access to the database and Medusa modules

import { Medusa } from "@medusajs/medusa"
import { loadEnv } from "@medusajs/framework/utils"
import { ContainerRegistrationKeys, Modules } from "@medusajs/framework/utils"

async function seedProducts() {
  console.log("=== Starting product seeding ===")
  
  // Load environment
  loadEnv(process.env.NODE_ENV || "production", process.cwd())
  
  // Initialize Medusa container
  const medusa = new Medusa({
    databaseUrl: process.env.DATABASE_URL,
    redisUrl: process.env.REDIS_URL,
    adminCors: process.env.ADMIN_CORS,
    storeCors: process.env.STORE_CORS,
    authCors: process.env.AUTH_CORS,
    jwtSecret: process.env.JWT_SECRET,
    cookieSecret: process.env.COOKIE_SECRET,
  })
  
  const container = await medusa.getContainer()
  
  // Get required modules
  const productModule = container.resolve(Modules.PRODUCT)
  const productCategoryModule = container.resolve(Modules.PRODUCT_CATEGORY)
  const regionModule = container.resolve(Modules.REGION)
  const currencyModule = container.resolve(Modules.CURRENCY)
  const salesChannelModule = container.resolve(Modules.SALES_CHANNEL)
  
  console.log("Modules resolved")
  
  // Check if products already exist
  const existingProducts = await productModule.listProducts({}, { take: 1 })
  if (existingProducts.length > 0) {
    console.log("Products already exist, skipping seed")
    return
  }
  
  console.log("No products found, seeding...")
  
  // Create region
  const [region] = await regionModule.createRegions([{
    name: "Argentina",
    currency_code: "ars",
    countries: ["ar"],
    payment_providers: [],
  }])
  console.log("Created region:", region.id)
  
  // Create sales channel
  const [salesChannel] = await salesChannelModule.createSalesChannels([{
    name: "Default Sales Channel",
    description: "Default sales channel for storefront",
  }])
  console.log("Created sales channel:", salesChannel.id)
  
  // Create default currency
  await currencyModule.createCurrencies([{
    code: "ars",
    symbol: "$",
    name: "Argentine Peso",
  }])
  console.log("Created currency: ars")
  
  // Load products from products.json
  const fs = await import("fs")
  const path = await import("path")
  const productsData = JSON.parse(
    fs.readFileSync(path.join(process.cwd(), "medusa-backend", "..", "data", "products.json"), "utf-8")
  )
  
  console.log(`Seeding ${productsData.length} products...`)
  
  for (const product of productsData) {
    try {
      // Create product category if needed
      let category = await productCategoryModule.listProductCategories({
        name: product.category
      })
      
      let categoryId
      if (category.length === 0) {
        const [newCategory] = await productCategoryModule.createProductCategories([{
          name: product.category,
          description: product.category,
          is_active: true,
        }])
        categoryId = newCategory.id
        console.log(`Created category: ${product.category}`)
      } else {
        categoryId = category[0].id
      }
      
      // Create product
      const [createdProduct] = await productModule.createProducts([{
        title: product.name,
        subtitle: product.description || "",
        description: product.description || "",
        handle: product.slug,
        status: "published",
        thumbnail: product.images[0] || null,
        images: product.images.map((url, i) => ({ url, rank: i })),
        category_ids: [categoryId],
        sales_channels: [{ id: salesChannel.id }],
        options: [
          {
            title: "Default",
            values: ["Default"],
          }
        ],
        variants: [
          {
            title: "Default",
            sku: product.sku,
            prices: [
              { amount: product.prices.precio_lista || 0, currency_code: "ars", region_id: region.id },
              { amount: product.prices.precio_efectivo || 0, currency_code: "ars", region_id: region.id },
            ],
            inventory_quantity: 100,
            manage_inventory: true,
          }
        ],
      }])
      
      console.log(`Created product: ${createdProduct.title} (${createdProduct.id})`)
    } catch (error) {
      console.error(`Error creating product ${product.name}:`, error.message)
    }
  }
  
  console.log("=== Seeding completed ===")
}

seedProducts()
  .then(() => {
    console.log("=== Seeding completed successfully ===")
    process.exit(0)
  })
  .catch((error) => {
    console.error("Seeding failed:", error)
    process.exit(1)
  }