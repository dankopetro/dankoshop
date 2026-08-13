import { MedusaContainer } from "@medusajs/framework";
import {
  ContainerRegistrationKeys,
} from "@medusajs/framework/utils";

/**
 * initial-data-seed.ts
 *
 * Este script de migración fue vaciado intencionalmente.
 * Los productos, categorías, precios y configuración de DankoShop
 * se gestionan desde el Excel maestro vía:
 *   python3 scripts/sync_excel_to_medusa.py
 *
 * NO crear productos, categorías ni regiones demo aquí.
 * Si este script corre en una DB nueva, NO debe alterar el catálogo.
 *
 * La región ARS, el canal de ventas y la publishable key
 * se crean via la API de Medusa Admin desde el script de sync.
 */
export default async function initial_data_seed({
  container,
}: {
  container: MedusaContainer;
}) {
  const logger = container.resolve(ContainerRegistrationKeys.LOGGER);
  logger.info("initial-data-seed: skipped (DankoShop manages catalog via Excel sync)");
}
