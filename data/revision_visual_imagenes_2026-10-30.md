# Revisión visual de imágenes — Medusa producción

**Fecha:** 2026-10-30
**Alcance:** los 516 productos publicados en Medusa producción (thumbnails asignados)
**Método:** auditoría estructural (`scripts/auditar_imagenes.py`) + revisión visual de
31 hojas de contacto (`scripts/contact_sheets.py`), cada miniatura etiquetada con su SKU,
agrupada por categoría y con banner auto-verificador del archivo.

## Resultado

**✅ 516/516 thumbnails revisados visualmente — CERO contaminación de contenido.**

Cada imagen coincide con el título de su producto y con la categoría a la que pertenece
(considerando que categorías como "Hogar/Baño" o "Accesorios" son catch-all con variedad
legítima: vajilla, tarros, cámaras de seguridad, sillas de oficina, etc.).

## Desglose por categoría

| Categoría | Productos | Hojas | Resultado |
|---|---|---|---|
| Hogar/Baño | 233 | 10 | ✅ limpio |
| Pequeños Electrodomésticos | 48 | 2 | ✅ limpio |
| Herramientas | 36 | 2 | ✅ limpio |
| Bicicletas | 35 | 2 | ✅ limpio |
| Cocinas/Hornos/Microondas | 32 | 2 | ✅ limpio |
| Accesorios | 27 | 2 | ✅ limpio |
| Heladeras/Freezers | 21 | 1 | ✅ limpio |
| Outdoor/Playa | 19 | 1 | ✅ limpio |
| Lavarropas/Secarropas | 17 | 1 | ✅ limpio |
| Juguetería | 14 | 1 | ✅ limpio |
| Celulares | 8 | 1 | ✅ limpio |
| Combos | 7 | 1 | ✅ limpio |
| TVs | 5 | 1 | ✅ limpio |
| Deportes | 4 | 1 | ✅ limpio |
| Gaming | 4 | 1 | ✅ limpio |
| Audio | 4 | 1 | ✅ limpio |
| Notebooks y Tablets | 2 | 1 | ✅ limpio |
| **TOTAL** | **516** | **31** | **✅** |

## Falsos positivos investigados (5)

Las señales de la revisión automática/por subagentes fueron verificadas una por una
contra el título real del producto:

| SKU | Categoría | Sospecha | Título real | Veredicto |
|---|---|---|---|---|
| 7047 | Herramientas | "ionizador solar entre herramientas" | Ionizador Solar Midow 6V/2W | ✅ imagen = título. Solo es categorización discutible |
| 9401 | Juguetería | "mesa de pool no es juguete" | Mesa de Pool Semi Pro Paño Bordo | ✅ imagen = título (juegos) |
| 9386 | Juguetería | "mesa de pool no es juguete" | Mesa de Pool Semi Pro Paño Verde | ✅ imagen = título (juegos) |
| 9694 | Juguetería | "mesa de ping pong no es juguete" | Mesa de Ping Pong | ✅ imagen = título (juegos) |
| 6745 | Hogar/Baño | "se ve una heladera" | Placard 2 Puertas 1 Cajón Vitta Blanco | ✅ el objeto PRINCIPAL es el placard blanco; la heladera es fondo de showroom (verificado con revisión independiente) |

## Auditoría estructural (informativo)

- 516 thumbnails descargados, 0 errores de descarga.
- 446 "alertas" estructurales = `FILENAME_UUID` / `FILENAME_NO_SKU`: falsos positivos,
  son subidas por WhatsApp/admin con nombres UUID o `whatsapp_image_...`. NO indican
  contaminación. Reporte: `data/auditoria_imagenes.json`.

## Conclusión

- **Producción (Medusa/Railway) es correcta y es la fuente de verdad.** No requiere cambios.
- La contaminación detectada en octubre 2026 (silla gamer/tablet entre celulares) existió
  SOLO en la carpeta en disco `data/products_images/` (archivos renombrados + productos
  ajenos), nunca en Medusa.
- `scripts/rebuild_local_images.py` dejó Medusa local 100% espejo de producción
  (516/516 thumbnails idénticos).

## Reproducir

```bash
python3 scripts/auditar_imagenes.py            # auditoría estructural + thumbnails
python3 scripts/contact_sheets.py              # hojas en /tmp/contact_sheets/
# revisar visualmente (o por subagente) cada hoja verificando banner + SKU
```
