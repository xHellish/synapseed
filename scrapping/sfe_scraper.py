"""
sfe_scraper.py
==============
Scraper unificado del SFE (Servicio Fitosanitario del Estado, Costa Rica).

Extrae los 3 registros públicos y los guarda en output/:
  - plaguicidas.csv    (N° Registro, Marca, Ingredientes, Registrante, Estado)
  - fertilizantes.csv  (Tipo, Clase, N° Registro, Marca, Ingredientes, Registrante)
  - lmr.csv            (columnas detectadas dinámicamente del encabezado)

Uso:
  pip install httpx beautifulsoup4
  python sfe_scraper.py
  python sfe_scraper.py --delay 1.5
  python sfe_scraper.py --max-pages 2 --only plaguicidas
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

BASE_URL = "https://app.sfe.go.cr"
HOME_URL = f"{BASE_URL}/SFEInsumos/aspx/Seguridad/Home.aspx"
OUT_DIR  = Path("output")

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "es-CR,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection":      "keep-alive",
}

# IDs de tabla/pager para Plaguicidas y Fertilizantes
TABLE_ID_DEFAULT = "ctl00_ContentPlaceHolder1_pbResultadosConsulta_gdv_Datos"
PAGER_DEFAULT    = "ctl00$ContentPlaceHolder1$pbResultadosConsulta$gdv_Datos"

# IDs de tabla/pager para LMR (tabla distinta, sin pbResultadosConsulta)
TABLE_ID_LMR = "ctl00_ContentPlaceHolder1_gdv_Datos"
PAGER_LMR    = "ctl00$ContentPlaceHolder1$gdv_Datos"


# ---------------------------------------------------------------------------
# Configuración de datasets
# ---------------------------------------------------------------------------

@dataclass
class Dataset:
    name:        str            # Etiqueta en consola
    menu_arg:    str            # __EVENTARGUMENT para el menú
    csv_file:    str            # Nombre del CSV de salida
    columns:     list[str]      # Nombres de columnas (vacío = autodetectar desde <th>)
    col_indices: list[int]      # Índices 0-based de los <td> a extraer
    table_id:    str = field(default="")   # ID de la tabla HTML (vacío = usar default)
    pager:       str = field(default="")   # __EVENTTARGET de paginación
    # Si True, los datos ya están en la página del menú sin necesitar POST extra
    direct:      bool = field(default=False)


DATASETS: list[Dataset] = [
    Dataset(
        name        = "Plaguicidas",
        menu_arg    = r"Registro\Plaguicidas\40120",
        csv_file    = "plaguicidas.csv",
        # 6 <td> por fila: [RADIO], N°Reg, Marca, Ingredientes, Registrante, Estado
        # Saltamos col 0 (radio) y extraemos las 5 restantes → índices 1..5
        columns     = ["numero_registro", "marca", "ingredientes", "registrante", "estado"],
        col_indices = [1, 2, 3, 4, 5],
        table_id    = TABLE_ID_DEFAULT,
        pager       = PAGER_DEFAULT,
    ),
    Dataset(
        name        = "Fertilizantes",
        menu_arg    = r"Registro\Fertilizantes\40132",
        csv_file    = "fertilizantes.csv",
        # 8 <td> por fila: [RADIO], Tipo, Clase, N°Reg, Marca, Ingredientes, Registrante, dup
        # Saltamos col 0 (radio) y col 7 (duplicado de N°Reg) → índices 1..6
        columns     = ["tipo", "clase", "numero_registro", "marca",
                       "ingredientes", "registrante"],
        col_indices = [1, 2, 3, 4, 5, 6],
        table_id    = TABLE_ID_DEFAULT,
        pager       = PAGER_DEFAULT,
    ),
    Dataset(
        name        = "Norma Nacional de LMR",
        menu_arg    = r"Residuos / LMR\Norma Nacional de LMR\40211",
        csv_file    = "lmr.csv",
        # PantallaSeleccion.aspx ya carga los datos directamente al entrar
        # Usa tabla y pager con ID diferente (sin pbResultadosConsulta)
        columns     = [],           # se detectan de los <th>
        col_indices = [],
        table_id    = TABLE_ID_LMR,
        pager       = PAGER_LMR,
        direct      = True,         # datos ya disponibles al llegar, sin POST extra
    ),
]


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def get_form_fields(html: str) -> dict[str, str]:
    """Extrae todos los campos de formulario necesarios para el POST."""
    soup = BeautifulSoup(html, "html.parser")
    fields: dict[str, str] = {}
    for inp in soup.find_all("input"):
        name = inp.get("name", "")
        if not name:
            continue
        t = inp.get("type", "text").lower()
        if t in ("submit", "button", "reset", "image"):
            continue
        if t in ("checkbox", "radio"):
            if inp.get("checked") is not None:
                fields[name] = inp.get("value", "on")
            continue
        fields[name] = inp.get("value", "")
    for sel in soup.find_all("select"):
        name = sel.get("name", "")
        if not name:
            continue
        chosen = sel.find("option", selected=True)
        opt = chosen or sel.find("option")
        fields[name] = opt.get("value", "") if opt else ""
    for ta in soup.find_all("textarea"):
        name = ta.get("name", "")
        if name:
            fields[name] = ta.get_text() or ""
    return fields


def post_form(session: httpx.Client, url: str, data: dict,
              referer: str) -> httpx.Response:
    """POST helper con headers correctos."""
    return session.post(url, data=data, headers={
        **HEADERS,
        "Referer":      referer,
        "Origin":       BASE_URL,
        "Content-Type": "application/x-www-form-urlencoded",
    })


def cell_text(td) -> str:
    t = td.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", t).strip()


# ---------------------------------------------------------------------------
# Parseo de la tabla gdv_Datos
# ---------------------------------------------------------------------------

def find_table(html: str, table_id: str):
    soup = BeautifulSoup(html, "html.parser")
    t = soup.find("table", {"id": table_id})
    return t or soup.find("table", id=re.compile(r"gdv_Datos$"))


def detect_columns(html: str, table_id: str) -> tuple[list[str], list[int]]:
    """Detecta columnas desde los <th> del encabezado (para LMR)."""
    t = find_table(html, table_id)
    if not t:
        return [], []
    for tr in t.find_all("tr"):
        ths = tr.find_all("th")
        if not ths:
            continue
        raw = [cell_text(th) for th in ths]
        # Omitir primera columna si está vacía (radio button)
        start = 1 if raw and not raw[0] else 0
        names = raw[start:]
        indices = list(range(start, start + len(names)))
        col_names = [re.sub(r"\s+", "_", n.lower()) for n in names]
        return col_names, indices
    return [], []


def parse_table(html: str, col_indices: list[int], table_id: str) -> list[list[str]]:
    """Extrae filas de datos del GridView.

    Filtra filas de paginación (que aparecen con "1 2 3 ..." o "...") y filas
    vacías. Considera una fila como paginación si:
      - Contiene únicamente enlaces a páginas (Page$N)
      - Su texto completo es solo números, puntos suspensivos o espacios
    """
    t = find_table(html, table_id)
    if not t:
        return []

    JUNK = {"javascript", "page$", "__dopostback"}
    records = []
    min_cols = (max(col_indices) + 1) if col_indices else 1

    for tr in t.find_all("tr"):
        # Saltar fila si tiene <th> (encabezado de tabla)
        if tr.find("th"):
            continue

        # Detectar fila de paginación: tiene SOLO enlaces a páginas
        anchors = tr.find_all("a", href=re.compile(r"Page\$", re.I))
        if anchors and len(anchors) == len(tr.find_all("td")):
            continue

        tds = tr.find_all("td")
        if len(tds) < min_cols:
            continue

        # Extraer las celdas pedidas
        row = [cell_text(tds[i]) for i in col_indices] if col_indices \
              else [cell_text(td) for td in tds]

        combined = " ".join(row).lower()
        if any(j in combined for j in JUNK):
            continue

        # Filtrar filas que son solo paginación simple (ej: "1 2 3 ...", "...")
        if re.fullmatch(r"[\s\d\.\,]+", combined) and not any(ch.isalpha() for ch in combined):
            continue

        # Saltar filas totalmente vacías
        if not any(row):
            continue

        records.append(row)

    return records


# ---------------------------------------------------------------------------
# Paginación
# ---------------------------------------------------------------------------

def next_page(html: str, current: int, table_id: str) -> Optional[int]:
    """Devuelve el siguiente número de página, o None si es la última."""
    t = find_table(html, table_id)
    if not t:
        return None
    pages: set[int] = set()
    for a in t.find_all("a", href=re.compile(r"Page\$")):
        m = re.search(r"Page\$(\d+)", a.get("href", ""))
        if m:
            pages.add(int(m.group(1)))
    if not pages:
        return None
    max_visible = max(pages)
    return current + 1 if current < max_visible else max_visible + 1


# ---------------------------------------------------------------------------
# Scraping de un dataset
# ---------------------------------------------------------------------------

def scrape_dataset(ds: Dataset, session: httpx.Client, delay: float,
                   max_pages: int = 0) -> list[dict]:
    print(f"\n{'─'*60}")
    print(f"  {ds.name}")
    print(f"{'─'*60}")

    # Paso 1: GET Home → POST menú
    home_html = session.get(HOME_URL).text
    r = post_form(session, HOME_URL, {
        **get_form_fields(home_html),
        "__EVENTTARGET":   "ctl00$Menu1",
        "__EVENTARGUMENT": ds.menu_arg,
    }, referer=HOME_URL)

    page_url  = str(r.url)
    page_html = r.text
    print(f"  URL: {page_url}")

    if r.status_code != 200:
        print(f"  [ERROR] HTTP {r.status_code} al navegar al menú")
        return []

    # Para datasets sin direct=True: POST Consultar → resultados
    if not ds.direct:
        r = post_form(session, page_url, {
            **get_form_fields(page_html),
            "__EVENTTARGET":                        "",
            "__EVENTARGUMENT":                      "",
            "ctl00$ContentPlaceHolder1$btnAceptar": "Consultar",
        }, referer=page_url)
        page_url  = str(r.url)
        page_html = r.text

        if r.status_code != 200 or "gdv_Datos" not in page_html:
            print(f"  [ERROR] No se obtuvieron resultados (HTTP {r.status_code})")
            return []

    # Para LMR (direct=True): los datos ya están en la respuesta del menú
    elif "gdv_Datos" not in page_html:
        print(f"  [ERROR] La página no contiene gdv_Datos")
        return []

    # Detectar columnas si no están definidas
    col_indices = list(ds.col_indices)
    columns     = list(ds.columns)
    if not columns:
        columns, col_indices = detect_columns(page_html, ds.table_id)
        print(f"  Columnas detectadas: {columns}")

    if not columns:
        print("  [ERROR] No se pudieron detectar columnas")
        return []

    # Iterar páginas
    all_rows: list[list[str]] = []
    page_n = 1

    while True:
        rows = parse_table(page_html, col_indices, ds.table_id)
        all_rows.extend(rows)
        print(f"  Pág {page_n:4d}: +{len(rows):3d} filas  (total: {len(all_rows):,})")

        # Límite de páginas (para pruebas)
        if max_pages and page_n >= max_pages:
            print(f"  [INFO] Límite de {max_pages} páginas alcanzado")
            break

        nxt = next_page(page_html, page_n, ds.table_id)
        if nxt is None:
            break

        time.sleep(delay)
        r = post_form(session, page_url, {
            **get_form_fields(page_html),
            "__EVENTTARGET":   ds.pager,
            "__EVENTARGUMENT": f"Page${nxt}",
        }, referer=page_url)
        page_url = str(r.url)

        if r.status_code != 200 or "gdv_Datos" not in r.text:
            if r.status_code != 500:
                print(f"  [WARN] HTTP {r.status_code} en pág {nxt}")
            break

        page_html = r.text
        page_n    = nxt

    # Deduplicar y convertir a dicts
    seen:   set[tuple] = set()
    result: list[dict] = []
    for row in all_rows:
        key = tuple(row)
        if key not in seen:
            seen.add(key)
            result.append(dict(zip(columns, row)))

    print(f"  Total únicos: {len(result):,}")
    return result


# ---------------------------------------------------------------------------
# Guardar CSV
# ---------------------------------------------------------------------------

def save_csv(records: list[dict], path: Path) -> None:
    if not records:
        print(f"  [WARN] Sin datos para {path.name}")
        return
    path.parent.mkdir(exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        w.writeheader()
        w.writerows(records)
    print(f"  → {path}  ({len(records):,} registros)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scraper SFE Costa Rica — Plaguicidas, Fertilizantes, LMR"
    )
    p.add_argument("--delay", type=float, default=1.2,
                   help="Segundos entre páginas (default: 1.2)")
    p.add_argument("--max-pages", type=int, default=0,
                   help="Limitar a N páginas por dataset (0 = sin límite, default: 0)")
    p.add_argument("--only", type=str, default="",
                   help="Solo procesar estos datasets separados por coma "
                        "(ej: 'plaguicidas,fertilizantes')")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    print("=" * 60)
    print(" SFE Scraper — Costa Rica")
    print(f" Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Delay:  {args.delay}s entre páginas")
    if args.max_pages:
        print(f" Max páginas: {args.max_pages}")
    if args.only:
        print(f" Solo: {args.only}")
    print("=" * 60)

    OUT_DIR.mkdir(exist_ok=True)

    only = {x.strip().lower() for x in args.only.split(",") if x.strip()}

    with httpx.Client(timeout=45.0, follow_redirects=True, headers=HEADERS) as session:
        session.get(HOME_URL)  # Inicializar sesión/cookies
        for ds in DATASETS:
            if only and ds.name.lower() not in only:
                continue
            try:
                records = scrape_dataset(ds, session, args.delay, args.max_pages)
                save_csv(records, OUT_DIR / ds.csv_file)
            except Exception as exc:
                print(f"\n  [ERROR] {ds.name}: {type(exc).__name__}: {exc}")
                import traceback; traceback.print_exc()

    print("\n" + "=" * 60)
    print(f" FIN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Archivos en: {OUT_DIR.resolve()}/")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



