const { Modules } = require("@medusajs/framework/utils")

module.exports = {
  default: async function increasePrices({ container }) {
    console.log("=== Increasing all variant prices by 10% ===")

    const productModule = container.resolve(Modules.PRODUCT)

    let offset = 0
    const limit = 50
    let totalUpdated = 0

    while (true) {
      const [products] = await productModule.listProducts({}, { take: limit, skip: offset })

      if (!products || products.length === 0) break

      for (const product of products) {
        if (!product.variants || product.variants.length === 0) continue

        for (const variant of product.variants) {
          if (!variant.prices || variant.prices.length === 0) continue

          const newPrices = variant.prices.map((price) => ({
            id: price.id,
            amount: Math.round(price.amount * 1.10),
            currency_code: price.currency_code || "ars",
          }))

          await productModule.updateProductVariants(variant.id, {
            prices: newPrices,
          })

          totalUpdated++
          console.log(`Updated: ${product.title} (${variant.sku}) - 10% increase`)
        }
      }

      if (products.length < limit) break
      offset += limit
    }

    console.log(`=== Done! Updated ${totalUpdated} variants ===`)
  },
}
