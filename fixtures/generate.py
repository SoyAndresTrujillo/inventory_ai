"""Generate the sample files used to test AI-driven product creation.

Every file describes products with its own vocabulary and shape - none of them
match the app's field names. The point is that the AI has to infer the mapping
to name / sku / price / quantity / attributes, and ask when something is missing.

    backend/.venv/bin/pip install -r backend/requirements-dev.txt
    backend/.venv/bin/python fixtures/generate.py
"""

import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

random.seed(7)  # reproducible fixtures


# --- CSV: Spanish retail export, COP prices, one row missing a price -------

CSV = """Descripcion del articulo,Ref. interna,Valor unitario,Cant. disponible,Marca,Pais de origen
Taladro percutor 750W,TP-750,289.900,14,Bosch,Alemania
Juego de destornilladores 12 pz,JD-12,54.500,37,Stanley,Estados Unidos
Cinta metrica 8m,CM-08,,52,Truper,Mexico
Nivel laser autonivelante,NL-360,412.000,6,Dewalt,Estados Unidos
"""


# --- JSON: API-style payload, nested, extra noise the AI must ignore -------

JSON_PAYLOAD = {
    "warehouse": {"id": "WH-BOG-02", "city": "Bogota", "manager": "L. Ramirez"},
    "synced_at": "2026-09-05T18:40:11Z",
    "page": 1,
    "items": [
        {
            "title": "Compresor de aire 50L",
            "code": "CA-50",
            "cost": {"amount": 1350000, "currency": "COP"},
            "stock": {"on_hand": 3, "reserved": 1},
            "manufacturer": "Truper",
            "made_in": {"country": "Mexico", "state": "Nuevo Leon"},
            "notes": "Requiere toma de 220V",
        },
        {
            "title": "Pistola de calor 2000W",
            "code": "PC-2000",
            "cost": {"amount": 178500, "currency": "COP"},
            "stock": {"on_hand": 11, "reserved": 0},
            "manufacturer": "Bosch",
            "made_in": {"country": "Alemania", "state": "Baden-Wurttemberg"},
        },
        {
            "title": "Multimetro digital TRMS",
            "code": "MD-TRMS",
            "cost": {"amount": 96000, "currency": "COP"},
            "manufacturer": "Fluke",
            "made_in": {"country": "Estados Unidos", "state": "Washington"},
            "notes": "Sin conteo de inventario en este corte",
        },
    ],
}


# --- XML: supplier catalog, data lives in attributes ------------------------

XML = """<?xml version="1.0" encoding="UTF-8"?>
<catalogoProveedor emitido="2026-09-03" proveedor="Ferreteria Andina S.A.S">
  <lote numero="L-2291">
    <articulo denominacion="Sierra circular 7 1/4" codigoBarras="SC-714" fabricante="Makita">
      <precioLista moneda="COP">615000</precioLista>
      <inventarioDisponible unidad="unidades">9</inventarioDisponible>
      <procedencia pais="Japon" ciudad="Nagoya"/>
    </articulo>
    <articulo denominacion="Amoladora angular 4 1/2" codigoBarras="AA-45" fabricante="Dewalt">
      <precioLista moneda="COP">329900</precioLista>
      <inventarioDisponible unidad="unidades">22</inventarioDisponible>
      <procedencia pais="China" ciudad="Suzhou"/>
    </articulo>
    <articulo denominacion="Set de brocas para concreto 10 pz" codigoBarras="SB-10C" fabricante="Irwin">
      <precioLista moneda="COP">87400</precioLista>
      <inventarioDisponible unidad="cajas">15</inventarioDisponible>
      <procedencia pais="Estados Unidos" ciudad="Huntersville"/>
    </articulo>
  </lote>
</catalogoProveedor>
"""


def write_pdf(path: Path) -> None:
    """A packing list: real product rows buried in shipping paperwork."""
    c = canvas.Canvas(str(path), pagesize=LETTER)
    width, height = LETTER
    y = height - 25 * mm

    c.setFont("Helvetica-Bold", 15)
    c.drawString(20 * mm, y, "IMPORTACIONES DEL CARIBE LTDA")
    c.setFont("Helvetica", 9)
    y -= 6 * mm
    c.drawString(20 * mm, y, "NIT 900.482.117-3  ·  Calle 72 #10-34, Barranquilla")
    y -= 5 * mm
    c.drawString(20 * mm, y, "PACKING LIST No. PL-2026-0918   ·   Contenedor MSKU-448210")
    y -= 5 * mm
    c.drawString(20 * mm, y, "Consignatario: Ferreteria Andina S.A.S   ·   Incoterm: CIF")

    y -= 12 * mm
    c.setFont("Helvetica-Bold", 9)
    headers = [
        (20 * mm, "DESCRIPCION"),
        (95 * mm, "PART No."),
        (125 * mm, "UNIT PRICE"),
        (155 * mm, "QTY"),
        (170 * mm, "ORIGIN"),
    ]
    for x, label in headers:
        c.drawString(x, y, label)
    y -= 2 * mm
    c.line(20 * mm, y, 195 * mm, y)

    rows = [
        ("Hidrolavadora 2200 PSI", "HL-2200", "USD 249.00", "8", "Italia"),
        ("Generador electrico 3.5 kVA", "GE-35", "USD 615.00", "4", "Japon"),
        ("Motobomba 2 pulgadas", "MB-02", "USD 188.50", "12", "China"),
        ("Soldador inverter 200A", "SI-200", "USD 143.90", "17", "Corea del Sur"),
    ]
    c.setFont("Helvetica", 9)
    for description, part, price, qty, origin in rows:
        y -= 7 * mm
        c.drawString(20 * mm, y, description)
        c.drawString(95 * mm, y, part)
        c.drawString(125 * mm, y, price)
        c.drawString(155 * mm, y, qty)
        c.drawString(170 * mm, y, origin)

    y -= 12 * mm
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(20 * mm, y, "Peso bruto total: 812 kg   ·   Bultos: 41   ·   Seguro incluido")
    y -= 5 * mm
    c.drawString(20 * mm, y, "Documento no valido como factura de venta.")
    c.save()


def write_image(path: Path) -> None:
    """A shelf label, rendered to look photographed rather than exported."""
    width, height = 900, 620
    image = Image.new("RGB", (width, height), (232, 229, 221))
    draw = ImageDraw.Draw(image)

    title = ImageFont.truetype(FONT_BOLD, 54)
    body = ImageFont.truetype(FONT, 34)
    small = ImageFont.truetype(FONT, 26)

    draw.rounded_rectangle((45, 45, width - 45, height - 45), radius=18, fill=(252, 251, 248))
    draw.rounded_rectangle((45, 45, width - 45, 150), radius=18, fill=(28, 40, 71))
    draw.text((75, 72), "DEPOSITO CENTRAL", font=ImageFont.truetype(FONT_BOLD, 40), fill=(255, 255, 255))

    draw.text((75, 195), "Pulidora de banco 6\"", font=title, fill=(24, 24, 27))
    draw.text((75, 275), "COD  PB-06", font=body, fill=(60, 60, 66))
    draw.text((75, 325), "$ 268.000  COP", font=body, fill=(24, 24, 27))
    draw.text((75, 375), "Existencias: 7 und", font=body, fill=(60, 60, 66))
    draw.text((75, 425), "Fabricante: Truper", font=small, fill=(90, 90, 96))
    draw.text((75, 465), "Origen: Mexico  ·  Monterrey", font=small, fill=(90, 90, 96))
    draw.text((75, 515), "Ubicacion pasillo 4 - estante B", font=small, fill=(140, 140, 146))

    # bar-code-ish block, so it reads as a real label
    x = 520
    while x < width - 90:
        bar = random.choice((3, 4, 7))
        draw.rectangle((x, 430, x + bar, 520), fill=(20, 20, 22))
        x += bar + random.choice((4, 6, 9))

    # photographed, not exported: slight rotation, blur and uneven light
    image = image.rotate(-1.4, resample=Image.BICUBIC, expand=False, fillcolor=(232, 229, 221))
    image = image.filter(ImageFilter.GaussianBlur(0.6))
    shade = Image.linear_gradient("L").resize((width, height)).point(lambda v: 200 + v // 5)
    image = Image.composite(image, Image.new("RGB", (width, height), (255, 255, 255)), shade)
    image.save(path, quality=88)


def main() -> None:
    (HERE / "products.csv").write_text(CSV, encoding="utf-8")
    (HERE / "products.json").write_text(json.dumps(JSON_PAYLOAD, indent=2, ensure_ascii=False), encoding="utf-8")
    (HERE / "products.xml").write_text(XML, encoding="utf-8")
    write_pdf(HERE / "packing-list.pdf")
    write_image(HERE / "shelf-label.jpg")
    for file in sorted(HERE.iterdir()):
        if file.name != "generate.py":
            print(f"{file.name:24} {file.stat().st_size:>7} bytes")


if __name__ == "__main__":
    main()
