const { Modules } = require("@medusajs/framework/utils")

module.exports = {
  default: async function increasePrices({ container }) {
    console.log("=== Increasing all variant prices by 10% ===")

    const productModule = container.resolve(Modules.PRODUCT)

    let offset = 0
    const limit = 50
    let totalUpdated = 0
    let totalSkipped = 0

    while (true) {
      const [products] = await productModule.listProducts({}, { take: limit, skip: offset })

      if (!products || products.length === 0) break

      for (const product of products) {
        if (!product.variants || product.variants.length === 0) continue

        for (const variant of product.variants) {
          if (!variant.prices || variant.prices.length === 0) {
            totalSkipped++
            continue
          }

          try {
            const newPrices = variant.prices.map((price) => ({
              id: price.id,
              amount: Math.round(price.amount * 1.10),
              currency_code: price.currency_code || "ars",
            }))

            await productModule.updateProductVariants(variant.id, {
              prices: newPrices,
            })

            totalUpdated++
            console.log(`OK: ${product.title} (${variant.sku}) - ${variant.prices[0].amount} -> ${newPrices[0].amount}`)
          } catch (err) {
            totalSkipped++
            console.error(`SKIP: ${product.title} (${variant.sku}) - ${err.message}`)
          }
        }
      }

      if (products.length < limit) break
      offset += limit
    }

    console.log(`=== Done! Updated: ${totalUpdated}, Skipped: ${totalSkipped} ===`)
  },
}
