# INFORME DE REVISIÓN DE IMÁGENES - DankoShop
## Fecha: 10 de Agosto de 2026

---

## RESUMEN EJECUTIVO

| Métrica | Valor |
|---------|-------|
| Total productos revisados | 117 |
| Total imágenes analizadas con OCR | 484 |
| Productos con imágenes desajustadas | 32 |
| Imágenes removidas (no correspondían) | 80 |
| Imágenes restantes (correctas) | 404 |
| Productos sin imagen | 0 |

---

## PROCESO REALIZADO

1. **Descarga masiva**: Se descargaron las 484 imágenes de los 117 productos desde Cloudinary
2. **OCR**: Se extrajo texto de cada imagen usando Tesseract (español + inglés)
3. **Cruce**: Se comparó el texto OCR contra el nombre/SKU de cada producto
4. **Detección**: Se identificaron 95 imágenes en 44 productos que no correspondían
5. **Corrección**: Se removieron 80 imágenes que claramente pertenecían a otro producto

---

## CORRECCIONES REALIZADAS (32 productos)

### Gaming / Electrónica
| SKU | Producto | Imágenes removidas | Motivo (texto OCR encontrado) |
|-----|----------|-------------------|-------------------------------|
| 6232 | Mesa Gamer GT-2310 | 2 | "Silla Gamer Ultrom" |
| 9347 | Celular Motorola G06 | 4 | "Silla Gamer" (x2), "Lavarropas Drean" (x2) |
| 6865 | Tablet Ultrom Alpha | 3 | "Silla Gamer" (x1), "Celular Motorola" (x2) |
| 8582 | Celular Enova E10 | 1 | "DURAX 12 PIEZAS" |

### Electrodomésticos - Heladeras/Freezers
| SKU | Producto | Imágenes removidas | Motivo |
|-----|----------|-------------------|--------|
| 2334 | Heladera Briket | 2 | "FRIGOBAR TELEFUNKEN" (x2) |
| 5671 | Frigobar Telefunken | 4 | "HELADERA TELEFUNKEN ONE DOOR" (x2), "HELADERA ENOVA" (x1), "HELADERA DREAN" (x1) |
| 5952 | Freezer Midea | 1 | "FRIGOBAR TELEFUNKEN" |
| 6322 | Bicicleta Infantil | 1 | "HELADERA DREAN NO FROST 306L" |

### Lavarropas
| SKU | Producto | Imágenes removidas | Motivo |
|-----|----------|-------------------|--------|
| 9479 | Lavarropas Drean | 1 | "DURAX 12 PIEZAS" |
| 6231 | Lavarropas Enova | 3 | "DURAX 12 PIEZAS" (x2), "Celular Enova" (x1) |

### Freidoras / Microondas (intercambiadas)
| SKU | Producto | Imágenes removidas | Motivo |
|-----|----------|-------------------|--------|
| 8391 | Microondas Smartlife 23L | 5 | Imágenes de freidoras Vitta/Midow/Futura |
| 5292 | Freidora Vitta 6.5L | 2 | Imágenes de microondas Vitta/Smartlife |
| 5709 | Freidora Vitta 2200W | 3 | Imágenes de microondas Vitta/Smartlife |
| 5947 | Freidora Futura Home 9.1L | 3 | Imágenes de microondas Vitta/Smartlife |
| 6163 | Freidora Vitta 11.8L | 3 | Imágenes de microondas Vitta/Smartlife |
| 6647 | Freidora Midow 3.5L | 3 | Imágenes de microondas Vitta |
| 6648 | Freidora Midow 3.5L (2) | 3 | Imágenes de microondas Vitta |
| 9063 | Freidora Smartlife 4.2L | 3 | Imágenes de microondas Vitta/Smartlife |
| 5290 | Freidora Vitta 8Lts | 3 | Imágenes de microondas Smartlife/Vitta |
| 5126 | Microondas Vitta Mecánico | 6 | Imágenes de freidoras Vitta/Midow/Futura |
| 5127 | Microondas Vitta Digital | 5 | Imágenes de freidoras Vitta/Midow/Smartlife |
| 7097 | Microondas Microsonic | 1 | "ANAFE DREAN" |
| 8392 | Microondas Smartlife 29L | 1 | "ANAFE DREAN" |
| 7200 | Anafe Drean Vitrocerámico | 1 | "MICROONDAS Microsonic" |

### Herramientas (intercambiadas)
| SKU | Producto | Imágenes removidas | Motivo |
|-----|----------|-------------------|--------|
| 5921 | Rotomartillo Kanji 800W | 2 | "LIJADORA ORBITAL CUADRADA KANJI" |
| 5401 | Termofusora Konan | 2 | "KIT TALADRO Y AMOLADORA" |
| 6884 | Taladro Percutor Konan | 1 | "AMOLADORA KONAN" |
| 7006 | Compresor Konan | 1 | "BOMBA CENTRÍFUGA KONAN" |

### Muebles / Otros
| SKU | Producto | Imágenes removidas | Motivo |
|-----|----------|-------------------|--------|
| 6749 | Chifonier 3 Cajones | 2 | "HIDROLAVADORA MIDOW" |
| 5752 | Reposera Mor | 1 | "CARRITO PLAYERO PLEGABLE" |

### Durax (vajillas/platos/vasos - intercambiadas)
| SKU | Producto | Acción |
|-----|----------|--------|
| 9447 | Vaso SixPack Point | Removidas 3, queda 1 correcta (PACKX6) |
| 9446 | Plato Hondo Fénix | Removidas 2, queda 1 correcta (PLATO HONDO) |
| 9445 | Plato Playo Fénix | Removidas 3, queda 1 correcta (PLATO PLAYO) |

---

## PRODUCTOS QUE NECESITAN ATENCIÓN MANUAL

### Con 1 sola imagen (podrían necesitar más):
- **9447** Vaso SixPack Point: 1 imagen (era 4)
- **9446** Plato Hondo Fénix: 1 imagen (era 3)
- **9445** Plato Playo Fénix: 1 imagen (era 4)
- **9347** Celular Motorola G06: 2 imágenes (era 6)
- **5127** Microondas Vitta Digital: 3 imágenes (era 8)
- **5921** Rotomartillo Kanji: 1 imagen (era 3)
- **5401** Termofusora Konan: 2 imágenes (era 4)
- **6749** Chifonier 3 Cajones: 2 imágenes (era 4)
- **7006** Compresor Konan: 2 imágenes (era 3)

### Imágenes que podrían estar en otro producto (revisar manualmente):
- **9448** Vaso FourPack: 2 imágenes, ambas parecen ser de otros productos Durax
- **9430** Escurridor Cool Bazar: 4 imágenes, todas son de platos Durax
- **5925** Lijadora Kanji: 2 imágenes, ambas son de rotomartillo
- **COMBO-02** Combo Argentino: 1 imagen de lavarropas (puede ser correcta si el combo incluye lavarropas)

---

## SCRIPTS REESCRITOS

### sync_excel_to_medusa.py (Excel → Medusa)
- Lee Excel con columnas: SKU, Artículo, Categoría, Descripción, Precio Lista, Precio Mayorista, Envío Grande
- Crea productos nuevos, actualiza existentes
- **NUNCA sobreescribe imágenes** — solo gestiona metadata, precios, categorías
- Calcula precios derivados desde Precio Mayorista
- Escribe ID de Medusa de vuelta en Excel

### sync_medusa_to_excel.py (Medusa → Excel)
- Lee 117 productos de Medusa
- Escribe Excel con 7 columnas formateadas (colores, centrado)
- Headers: SKU (rojo), Artículo (naranja), Categoría (verde), Descripción (azul), Precio Lista (púrpura), Precio Mayorista (naranja), Envío Grande (cyan)
- Fila congelada + autofiltro
- Columna oculta con ID de Medusa

---

## ESTADO FINAL

| Métrica | Antes | Después |
|---------|-------|---------|
| Total imágenes | 484 | 404 |
| Imágenes correctas | ~404 | 404 |
| Imágenes en producto incorrecto | ~80 | 0 |
| Productos sin imagen | 0 | 0 |

**Nota**: Las 80 imágenes removidas seguían existiendo en Cloudinary. Si algún producto quedó con pocas imágenes, las imágenes correctas pueden estar en:
1. El Excel backup: `excel/Productos_Maestro_backup_10ago.xlsx`
2. El JSON de backup: `data/medusa_backup_10ago.json`
3. Se deben subir manualmente via Medusa admin para los productos marcados
