import { loadEnv, defineConfig } from '@medusajs/framework/utils'

loadEnv(process.env.NODE_ENV || 'development', process.cwd())

module.exports = defineConfig({
  projectConfig: {
    databaseUrl: process.env.DATABASE_URL,
    http: {
      storeCors: process.env.STORE_CORS || "http://localhost:3000,https://dankoshop.com.ar,https://www.dankoshop.com.ar,https://dankoshop.vercel.app",
      adminCors: process.env.ADMIN_CORS || "http://localhost:9000,http://localhost:7001",
      authCors: process.env.AUTH_CORS || "http://localhost:3000,http://localhost:9000,https://dankoshop.com.ar,https://www.dankoshop.com.ar,https://dankoshop.vercel.app",
      jwtSecret: process.env.JWT_SECRET || "super-secret-jwt",
      cookieSecret: process.env.COOKIE_SECRET || "super-secret-cookie",
    }
  },
  modules: [
    // MercadoPago payment provider - uncomment after installing @medusajs/payment-mercadopago
    // {
    //   resolve: "@medusajs/payment-mercadopago",
    //   options: {
    //     access_token: process.env.MERCADOPAGO_ACCESS_TOKEN,
    //     public_key: process.env.MERCADOPAGO_PUBLIC_KEY,
    //     webhook_secret: process.env.MERCADOPAGO_WEBHOOK_SECRET,
    //   },
    // },
  ],
})