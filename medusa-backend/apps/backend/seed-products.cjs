const { Modules } = require("@medusajs/framework/utils")
const {
  createProductCategoriesWorkflow,
  createProductOptionsWorkflow,
  createProductsWorkflow,
  createUserAccountWorkflow,
} = require("@medusajs/medusa/core-flows")
const fs = require("fs")

const PRODUCTS_FILE = process.env.SEED_PRODUCTS_FILE || "/app/data/products.json"
const IMAGE_URLS_FILE = process.env.SEED_IMAGE_URLS_FILE || "/app/data/image_urls.json"

function slugify(input) {
  return String(input)
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 200)
}

module.exports = {
  default: async function seedProducts({ container }) {
    console.log("=== Starting product seeding ===")

    console.log("=== Ensuring admin user exists ===")
    try {
      await createUserAccountWorkflow(container).run({
        input: {
          email: "admin@dankoshop.com",
          password: "supersecret",
        },
      })
      console.log("Admin user created: admin@dankoshop.com")
    } catch (e) {
      console.log("Admin user already exists or skipped:", e.message)
    }

    const productModule = container.resolve(Modules.PRODUCT)
    const regionModule = container.resolve(Modules.REGION)
    const currencyModule = container.resolve(Modules.CURRENCY)
    const salesChannelModule = container.resolve(Modules.SALES_CHANNEL)

    console.log("Modules resolved")

    const productsData = JSON.parse(fs.readFileSync(PRODUCTS_FILE, "utf-8"))
    const firstHandle = slugify(productsData[0].sku)
    const existing = await productModule.listProducts(
      { handle: firstHandle },
      { take: 1 }
    )
    if (existing.length > 0) {
      console.log(`Products with handle ${firstHandle} already exist, skipping seed`)
      return
    }

    console.log("No DankoShop products found, seeding...")

    let imageUrls = {}
    try {
      imageUrls = JSON.parse(fs.readFileSync(IMAGE_URLS_FILE, "utf-8"))
    } catch (e) {
      console.warn("Could not load image_urls.json, falling back to local paths:", e.message)
    }

    let region = (await regionModule.listRegions({}, { take: 1 }))[0]
    if (!region) {
      const [created] = await regionModule.createRegions([{
        name: "Argentina",
        currency_code: "ars",
        countries: ["ar"],
        payment_providers: [],
      }])
      region = created
    }
    console.log("Using region:", region.id)

    let salesChannel = (await salesChannelModule.listSalesChannels({}, { take: 1 }))[0]
    if (!salesChannel) {
      const [created] = await salesChannelModule.createSalesChannels([{
        name: "Default Sales Channel",
        description: "Default sales channel for storefront",
      }])
      salesChannel = created
    }
    console.log("Using sales channel:", salesChannel.id)

    const currencyExists = await currencyModule.listCurrencies({ code: "ars" }, { take: 1 })
    if (currencyExists.length === 0) {
      await currencyModule.createCurrencies([{
        code: "ars",
        symbol: "$",
        name: "Argentine Peso",
      }])
      console.log("Created currency: ars")
    } else {
      console.log("Currency ars already exists")
    }

    const categoryMap = {}
    const categoriesToCreate = [...new Set(productsData.map((p) => p.category).filter(Boolean))]
    const existingCategories = await productModule.listProductCategories({}, { take: 200 })
    for (const c of existingCategories) {
      categoryMap[c.name] = c.id
    }
    const missingCategories = categoriesToCreate.filter((name) => !categoryMap[name])
    if (missingCategories.length > 0) {
      const { result } = await createProductCategoriesWorkflow(container).run({
        input: {
          product_categories: missingCategories.map((name) => ({
            name,
            description: name,
            is_active: true,
          })),
        },
      })
      for (const c of result) {
        categoryMap[c.name] = c.id
        console.log(`Created category: ${c.name}`)
      }
    }

    const { result: optionResult } = await createProductOptionsWorkflow(container).run({
      input: {
        product_options: [
          {
            title: "Default",
            values: ["Default"],
          },
        ],
      },
    })
    const defaultOption = optionResult[0]
    console.log("Created default product option:", defaultOption.id)

    console.log(`Seeding ${productsData.length} products...`)

    let createdCount = 0
    let failedCount = 0

    for (const product of productsData) {
      try {
        const images = (imageUrls[product.sku] || (Array.isArray(product.images) ? product.images : [])).slice(0, 10)
        const handle = slugify(product.sku)

        const { result } = await createProductsWorkflow(container).run({
          input: {
            products: [
              {
                title: product.name,
                subtitle: product.description || "",
                description: product.description || "",
                handle,
                status: "published",
                thumbnail: images[0] || null,
                images: images.map((url) => ({ url })),
                category_ids: product.category ? [categoryMap[product.category]] : undefined,
                sales_channels: [{ id: salesChannel.id }],
                options: [{ id: defaultOption.id }],
                variants: [
                  {
                    title: "Default",
                    sku: product.sku,
                    options: { Default: "Default" },
                    prices: [
                      { amount: product.prices.precio_lista || 0, currency_code: "ars", region_id: region.id },
                    ],
                  },
                ],
              },
            ],
          },
        })

        console.log(`Created product: ${result[0].title} (${result[0].id})`)
        createdCount++
      } catch (error) {
        console.error(`Error creating product ${product.name}:`, error.message)
        failedCount++
      }
    }

    console.log(`=== Seeding completed: ${createdCount} created, ${failedCount} failed ===`)
  },
}
