import { randomBytes } from "crypto"
import { loadEnv, defineConfig } from '@medusajs/framework/utils'

loadEnv(process.env.NODE_ENV || 'development', process.cwd())

// Secrets: NUNCA defaults publicos (el "super-secret-jwt" por defecto permitia
// forjar tokens de admin). Si faltan las variables (p.ej. en el build de Docker,
// donde Railway no inyecta env vars), se genera un valor aleatorio por proceso:
// imposible de adivinar, y como cambia en cada arranque invalida sesiones — por
// eso en runtime debe venir de la env var JWT_SECRET / COOKIE_SECRET.
const jwtSecret = process.env.JWT_SECRET || randomBytes(32).toString("hex")
const cookieSecret = process.env.COOKIE_SECRET || randomBytes(32).toString("hex")
if (!process.env.JWT_SECRET || !process.env.COOKIE_SECRET) {
  console.warn(
    "Aviso: JWT_SECRET / COOKIE_SECRET no seteados; usando valores aleatorios " +
    "(las sesiones se invalidan al reiniciar). Setealos en las variables del servicio."
  )
}

module.exports = defineConfig({
  projectConfig: {
    databaseUrl: process.env.DATABASE_URL,
    http: {
      storeCors: process.env.STORE_CORS || "http://localhost:3000,https://dankoshop.com.ar,https://www.dankoshop.com.ar,https://dankoshop.vercel.app",
      adminCors: process.env.ADMIN_CORS || "http://localhost:9000,http://localhost:7001",
      authCors: process.env.AUTH_CORS || "http://localhost:3000,http://localhost:9000,https://dankoshop.com.ar,https://www.dankoshop.com.ar,https://dankoshop.vercel.app",
      jwtSecret,
      cookieSecret,
    }
  },
  modules: [
    // Cloudinary file storage provider
    {
      resolve: "@medusajs/medusa/file",
      options: {
        providers: [
          {
            resolve: "./src/providers/cloudinary",
            id: "cloudinary",
            options: {
              apiKey: process.env.CLOUDINARY_API_KEY,
              apiSecret: process.env.CLOUDINARY_API_SECRET,
              cloudName: process.env.CLOUDINARY_CLOUD_NAME,
              folderName: "dankoshop",
              secure: true,
            },
          },
        ],
      },
    },
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