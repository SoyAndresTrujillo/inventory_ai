# Test fixtures for AI product creation

Five files describing products, none of them using the app's field names. They exist
to test whether the AI infers the mapping to `name` / `sku` / `price` / `quantity` /
attributes on its own, and asks when data is missing.

Regenerate with:

```bash
backend/.venv/bin/pip install -r backend/requirements-dev.txt
backend/.venv/bin/python fixtures/generate.py
```

| File                | Shape                          | What it hides                                                        |
| ------------------- | ------------------------------ | -------------------------------------------------------------------- |
| `products.csv`      | Spanish retail export, 4 rows  | `Valor unitario` is COP with dot thousands (`289.900`); one row has **no price** |
| `products.json`     | Nested API payload, 3 items    | Price under `cost.amount`, stock under `stock.on_hand`; one item has **no stock**; warehouse/sync noise to ignore |
| `products.xml`      | Supplier catalog, 3 articles   | Data lives in **attributes**, not elements; one item counted in `cajas`, not units |
| `packing-list.pdf`  | Shipping paperwork, 4 rows     | Product table buried in addresses, container numbers, weights; prices in **USD** |
| `shelf-label.jpg`   | Photographed shelf label       | One product, slightly rotated and blurred, barcode block, aisle location that is not a product field |

No two files share a product, so you can import all five and get 15 distinct products.

## What good behavior looks like

- Infers `Marca` / `manufacturer` / `fabricante` are the same concept, and asks before
  creating it as a category (categories must exist first).
- Reads `289.900` as 289900 COP, not 289.90.
- Notices the missing price (CSV `Cinta metrica 8m`) and missing stock
  (JSON `Multimetro digital TRMS`) and asks instead of inventing zeros.
- Treats `unidad="cajas"` as worth mentioning rather than silently equating to units.
- Ignores the packing-list header, weights and the label's aisle location.
- Ends with a summary of what it created and what it skipped.

## Provider support

| File            | ollama (`glm-4.7-flash`) | openai / anthropic (vision) |
| --------------- | ------------------------ | --------------------------- |
| csv, json, xml  | yes                      | yes                         |
| pdf, jpg        | rejected with an error   | yes                         |

The local default is text-only, so `packing-list.pdf` and `shelf-label.jpg` come back as
a 502 explaining why. Switch `AI_PROVIDER` in `backend/.env` (or set `AI_VISION=1` with a
vision-capable local model) to test those two.
