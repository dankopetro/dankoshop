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
    console.log("=== Starting product seeding (upsert) ===")

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

    const productsData = JSON.parse(fs.readFileSync(PRODUCTS_FILE, "utf-8"))

    let imageUrls = {}
    try {
      imageUrls = JSON.parse(fs.readFileSync(IMAGE_URLS_FILE, "utf-8"))
    } catch (e) {
      console.warn("Could not load image_urls.json, falling back to local paths:", e.message)
    }

    // --- Ensure Argentina region with ARS (pesos) ---
    let region = (await regionModule.listRegions({ currency_code: "ars" }, { take: 1 }))[0]
    if (!region) {
      const [created] = await regionModule.createRegions([{
        name: "Argentina",
        currency_code: "ars",
        countries: ["ar"],
        payment_providers: [],
      }])
      region = created
      console.log("Created Argentina region:", region.id)
    } else {
      console.log("Argentina region found:", region.id)
    }

    // --- Ensure sales channel ---
    let salesChannel = (await salesChannelModule.listSalesChannels({}, { take: 1 }))[0]
    if (!salesChannel) {
      const [created] = await salesChannelModule.createSalesChannels([{
        name: "Default Sales Channel",
        description: "Default sales channel for storefront",
      }])
      salesChannel = created
    }
    console.log("Using sales channel:", salesChannel.id)

    // --- Ensure ARS currency ---
    const currencyExists = await currencyModule.listCurrencies({ code: "ars" }, { take: 1 })
    if (currencyExists.length === 0) {
      await currencyModule.createCurrencies([{
        code: "ars",
        symbol: "$",
        name: "Argentine Peso",
      }])
      console.log("Created currency: ars")
    }

    // --- Categories ---
    const categoryMap = {}
    const categoriesToCreate = [...new Set(productsData.map((p) => p.category).filter(Boolean))]
    const existingCategories = await productModule.listProductCategories({}, { take: 200 })
    for (const c of existingCategories) {
      categoryMap[c.name] = c.id
    }
    const missingCategories = categoriesToCreate.filter((name) => !categoryMap[name])
    if (missingCategories.length > 0) {
      try {
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
      } catch (e) {
        console.warn("Some categories already exist, refreshing map:", e.message)
        const refreshed = await productModule.listProductCategories({}, { take: 200 })
        for (const c of refreshed) {
          categoryMap[c.name] = c.id
        }
      }
    }

    // --- Default option (reuse if already exists) ---
    let defaultOption = (await productModule.listProductOptions({ title: "Default" }, { take: 1 }))[0]
    if (!defaultOption) {
      try {
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
        defaultOption = optionResult[0]
      } catch (e) {
        console.warn("Default option may already exist:", e.message)
        defaultOption = (await productModule.listProductOptions({ title: "Default" }, { take: 1 }))[0]
      }
    }
    console.log("Using default option:", defaultOption.id)

    // --- Load existing products by handle ---
    const existingProducts = await productModule.listProducts({}, { take: 500, select: ["id", "handle", "title"] })
    const existingByHandle = {}
    for (const p of existingProducts) {
      existingByHandle[p.handle] = p.id
    }
    console.log(`Found ${Object.keys(existingByHandle).length} existing products in Medusa`)

    let createdCount = 0
    let updatedCount = 0
    let failedCount = 0

    for (const product of productsData) {
      try {
        const sku = product.sku
        const handle = slugify(sku)
        const images = (imageUrls[sku] || (Array.isArray(product.images) ? product.images : [])).slice(0, 10)
        const prices = product.prices || {}

        const metadata = {
          precio_lista: prices.precio_lista ?? null,
          precio_efectivo: prices.precio_efectivo ?? null,
          precio_transferencia: prices.precio_transferencia ?? null,
          precio_mayorista: prices.precio_mayorista ?? null,
          precio_mayorista_transferencia: prices.precio_mayorista_transferencia ?? null,
          cuotas: prices.cuotas ?? null,
          cuota_valor: prices.cuota_valor ?? null,
        }
        Object.keys(metadata).forEach((k) => {
          if (metadata[k] === null || metadata[k] === "") delete metadata[k]
        })

        const categoryIds = product.category && categoryMap[product.category] ? [categoryMap[product.category]] : []

        const baseProduct = {
          title: product.name,
          subtitle: product.description || "",
          description: product.description || "",
          handle,
          status: "published",
          thumbnail: images[0] || null,
          images: images.map((url) => ({ url })),
          category_ids: categoryIds,
          sales_channels: [{ id: salesChannel.id }],
          options: [{ id: defaultOption.id }],
          metadata,
          variants: [
            {
              title: "Default",
              sku,
              options: { Default: "Default" },
              prices: [
                { amount: Math.round(Number(prices.precio_lista) || 0), currency_code: "ars", region_id: region.id },
              ],
            },
          ],
        }

        if (existingByHandle[handle]) {
          // Update existing product metadata only (variant already exists)
          await productModule.updateProducts({ id: existingByHandle[handle] }, { metadata })
          updatedCount++
          console.log(`Updated metadata: ${product.name} (${handle})`)
        } else {
          const { result } = await createProductsWorkflow(container).run({
            input: { products: [baseProduct] },
          })
          console.log(`Created product: ${result[0].title} (${result[0].id})`)
          createdCount++
        }
      } catch (error) {
        console.error(`Error processing product ${product.name}:`, error.message)
        failedCount++
      }
    }

    console.log(`=== Seeding completed: ${createdCount} created, ${updatedCount} updated, ${failedCount} failed ===`)
  },
}
