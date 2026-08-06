import { Medusa } from "@medusajs/medusa"
import { loadEnv } from "@medusajs/framework/utils"
import { Modules } from "@medusajs/framework/utils"

const PRODUCTS_FILE = "/app/data/products.json"
const IMAGE_URLS_FILE = "/app/data/image_urls.json"

async function seedProducts() {
  console.log("=== Starting product seeding ===")

  loadEnv(process.env.NODE_ENV || "production", process.cwd())

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

  const productModule = container.resolve(Modules.PRODUCT)
  const productCategoryModule = container.resolve(Modules.PRODUCT_CATEGORY)
  const regionModule = container.resolve(Modules.REGION)
  const currencyModule = container.resolve(Modules.CURRENCY)
  const salesChannelModule = container.resolve(Modules.SALES_CHANNEL)

  console.log("Modules resolved")

  const existingProducts = await productModule.listProducts({}, { take: 1 })
  if (existingProducts.length > 0) {
    console.log("Products already exist, skipping seed")
    return
  }

  console.log("No products found, seeding...")

  const [region] = await regionModule.createRegions([{
    name: "Argentina",
    currency_code: "ars",
    countries: ["ar"],
    payment_providers: [],
  }])
  console.log("Created region:", region.id)

  const [salesChannel] = await salesChannelModule.createSalesChannels([{
    name: "Default Sales Channel",
    description: "Default sales channel for storefront",
  }])
  console.log("Created sales channel:", salesChannel.id)

  await currencyModule.createCurrencies([{
    code: "ars",
    symbol: "$",
    name: "Argentine Peso",
  }])
  console.log("Created currency: ars")

  const fs = await import("fs")
  const productsData = JSON.parse(fs.readFileSync(PRODUCTS_FILE, "utf-8"))
  let imageUrls = {}
  try {
    imageUrls = JSON.parse(fs.readFileSync(IMAGE_URLS_FILE, "utf-8"))
  } catch (e) {
    console.warn("Could not load image_urls.json, falling back to local paths:", e.message)
  }

  console.log(`Seeding ${productsData.length} products...`)

  for (const product of productsData) {
    try {
      let category = await productCategoryModule.listProductCategories({
        name: product.category,
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

      let images = imageUrls[product.sku] || []
      if (images.length === 0 && Array.isArray(product.images)) {
        images = product.images
      }
      images = images.slice(0, 10)

      const [createdProduct] = await productModule.createProducts([{
        title: product.name,
        subtitle: product.description || "",
        description: product.description || "",
        handle: product.sku,
        status: "published",
        thumbnail: images[0] || null,
        images: images.map((url, i) => ({ url, rank: i })),
        category_ids: [categoryId],
        sales_channels: [{ id: salesChannel.id }],
        options: [
          {
            title: "Default",
            values: ["Default"],
          },
        ],
        variants: [
          {
            title: "Default",
            sku: product.sku,
            prices: [
              { amount: product.prices.precio_lista || 0, currency_code: "ars", region_id: region.id },
            ],
            inventory_quantity: 100,
            manage_inventory: true,
          },
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
  })
