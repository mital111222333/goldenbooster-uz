"""Static site generator for goldenbooster.uz.

Usage:  python build.py        -> writes the site into ./dist
Data:   src/data/products_source.json (scraped EN+RU), uz.json, ru_extra.json, i18n.json, config.json
"""
import json
import re
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
SRC, DIST = ROOT / "src", ROOT / "dist"
LANGS = ["uz", "ru"]


def load(name):
    return json.loads((SRC / "data" / name).read_text(encoding="utf-8"))


CFG = load("config.json")
UZ, RU_EXTRA, T = load("uz.json"), load("ru_extra.json"), load("i18n.json")

CATEGORIES = [  # (source id, slug, uz, ru)
    (30, "high-performance", "Yuqori samarali moylar", "Высокопроизводительные масла"),
    (31, "passenger", "Yengil avtomobillar va SUV", "Легковые автомобили и SUV"),
    (29, "heavy-duty", "Yuk mashinalari va maxsus texnika", "Грузовики и спецтехника"),
    (1, "moto", "Mototsikl moylari", "Мотомасла"),
    (2, "transmission", "Transmissiya moylari", "Трансмиссионные масла"),
    (3, "atf-cvt", "ATF va variator suyuqliklari", "Жидкости для АКПП и вариаторов"),
    (4, "hydraulic", "Gidravlika moylari", "Гидравлические масла"),
    (37, "marine", "Dengiz moylari", "Судовые масла"),
    (34, "additives", "Qoʻshimchalar", "Присадки"),
    (36, "antifreeze", "Antifriz", "Антифриз"),
    (35, "brake-fluid", "Tormoz suyuqligi", "Тормозная жидкость"),
    (32, "car-care", "Avtokimyo", "Автохимия"),
]
CAT_BY_ID = {c[0]: {"id": c[0], "slug": c[1], "uz": c[2], "ru": c[3]} for c in CATEGORIES}

SERIES = {
    "GOLD": {"color": "#c9a24a", "tag": "100% PAO",
             "uz": "Kuchli va sport dvigatellari uchun", "ru": "Для мощных и спортивных двигателей"},
    "BLUE": {"color": "#4a6fd1", "tag": "100% SYNTH",
             "uz": "Zamonaviy Euro 5–6 va DPF uchun", "ru": "Для современных Euro 5–6 и DPF"},
    "RED": {"color": "#c0392b", "tag": "SYNTHETIC",
            "uz": "Har kuni jim va bir tekis ishlash", "ru": "Тихая и ровная работа каждый день"},
    "PURPLE": {"color": "#7d4fa8", "tag": "SEMI-SYNTH",
               "uz": "Benzin, dizel va gaz uchun butun yil himoya", "ru": "Всесезонная защита для бензина, дизеля и газа"},
    "HYBRID": {"color": "#2e9e6a", "tag": "API SP",
               "uz": "Gibrid avtomobillar uchun", "ru": "Для гибридных автомобилей"},
    "ULTRA HEAVY": {"color": "#1a1714", "tag": "DIESEL",
                    "uz": "Yuk mashinalari, avtobuslar va maxsus texnika", "ru": "Грузовики, автобусы и спецтехника"},
}

MARINE_SPECS = {238: "SAE 40 · TBN ≈ 12 · TPEO", 239: "SAE 40 · TBN ≈ 12 · TPEO",
                240: "SAE 40 · TBN ≈ 30 · TPEO", 241: "SAE 40 · TBN ≈ 30 · TPEO"}
MARINE_PACK = {238: "200 L", 239: "FlexiBag", 240: "200 L", 241: "FlexiBag"}


def slugify(name):
    s = re.sub(r"^GOLDEN BOOSTER\s+", "", name, flags=re.I).lower()
    s = s.replace("&", "and").replace("/", " ")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def bullets(text):
    out = []
    for line in (text or "").split("\n"):
        line = re.sub(r"^\s*[●•·\-]\s*", "", line).strip()
        if line:
            out.append(line)
    return out


def spec_text(sections):
    for k, v in sections.items():
        if "Specification" in k or "규격" in k or "Характ" in k:
            return v.strip()
    return ""


def localize_spec(text, lang):
    if lang == "uz":
        text = re.sub(r"\band others\.?", "va boshqalar.", text)
        text = re.sub(r"Observe manufacturer manual for references\.?",
                      "Batafsil maʼlumot uchun avtomobil qoʻllanmasiga qarang.", text)
    return re.sub(r"\s*\n\s*", " ", text).strip()


def parse_ru(ru):
    """RU summary looks like: type lines / blank line / description / blank line / packaging line."""
    blocks = [b.strip() for b in ru["summary"].split("\n\n") if b.strip()]
    blocks = [b for b in blocks if not b.startswith("Варианты упаковки")]
    if blocks:
        type_ = " · ".join(ln.strip(" /") for ln in blocks[0].split("\n") if ln.strip(" /"))
        type_ = type_.replace(", · ", ", ").replace(" · +", " +")
    else:
        type_ = ru["type"]
    desc = " ".join(blocks[1:]) if len(blocks) > 1 else ""
    sec = ru["sections"]
    feats = next((bullets(v) for k, v in sec.items() if k.startswith("Преимущ")), [])
    usage = next((v for k, v in sec.items() if k.startswith("Инструк")), "")
    return {"type": type_, "summary": re.sub(r"\s+", " ", desc).strip(), "features": feats,
            "usage": "\n".join(bullets(usage)), "specs": localize_spec(spec_text(sec), "ru")}


def series_of(name):
    for s in SERIES:
        if f" {s} " in f" {name.upper()} ":
            return s
    return None


def build_products():
    products = []
    for p in load("products_source.json"):
        idx = p["idx"]
        name = re.sub(r"\s+", " ", p["name"]).strip()
        uz = UZ[str(idx)]
        if p["ru"]:
            ru = parse_ru(p["ru"])
            if not ru["summary"]:
                ru["summary"] = ru["type"]
        else:
            e = RU_EXTRA[str(idx)]
            ru = {"type": e["type"], "summary": e["summary"], "features": e["features"], "usage": "",
                  "specs": MARINE_SPECS[idx]}
        specs_uz = MARINE_SPECS.get(idx) or localize_spec(spec_text(p["en"]["sections"]), "uz")
        visc = re.search(r"\b(\d{1,2}W-\d{2,3}|HD \d{2}|AW 32/46/68/100|DOT-4|2T|4T 10W-40)\b", name)
        pack = p.get("packaging") or MARINE_PACK.get(idx, "")
        products.append({
            "idx": idx, "slug": slugify(name), "name": name,
            "short": re.sub(r"^GOLDEN BOOSTER\s+", "", name, flags=re.I),
            "image": Path(p["image"]).name if p["image"] else "",
            "cat": CAT_BY_ID[p["category_id"]], "series": series_of(name),
            "visc": visc.group(1) if visc else "",
            "packaging": [x.strip().replace("Л", " L").replace(",", ".") for x in pack.split("/") if x.strip()],
            "uz": {"type": uz["type"], "summary": uz["summary"], "features": uz["features"],
                   "usage": uz.get("usage", ""), "specs": specs_uz},
            "ru": ru,
        })
    order = {c[0]: i for i, c in enumerate(CATEGORIES)}
    products.sort(key=lambda x: (order[x["cat"]["id"]], x["idx"]))
    return products


def url(lang, path=""):
    path = path.strip("/")
    base = "/" if lang == "uz" else "/ru/"
    return base + (path + "/" if path else "")


def render_all():
    env = Environment(loader=FileSystemLoader(SRC / "templates"), autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    products = build_products()
    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "assets").mkdir(parents=True)
    shutil.copytree(SRC / "static", DIST / "assets", dirs_exist_ok=True)
    (DIST / ".nojekyll").write_text("", encoding="utf-8")  # GitHub Pages: serve files as-is

    cats = []
    for c in CATEGORIES:
        cc = dict(CAT_BY_ID[c[0]])
        cc["count"] = sum(1 for p in products if p["cat"]["id"] == c[0])
        cats.append(cc)
    series_cards = []
    for s, meta in SERIES.items():
        items = [p for p in products if p["series"] == s]
        series_cards.append({"key": s, **meta, "image": items[0]["image"], "first": items[0],
                             "grades": " · ".join(dict.fromkeys(p["visc"] for p in items if p["visc"]))})

    pages = [("", "index.html", {"page": "home"}), ("catalog", "catalog.html", {"page": "catalog"}),
             ("technology", "technology.html", {"page": "technology"}),
             ("company", "company.html", {"page": "company"}), ("contacts", "contacts.html", {"page": "contacts"})]
    for p in products:
        related = [q for q in products if q["cat"]["id"] == p["cat"]["id"] and q["idx"] != p["idx"]][:8]
        pages.append((f"catalog/{p['slug']}", "product.html", {"page": "product", "p": p, "related": related}))

    def ctx(lang, path, extra):
        other = "ru" if lang == "uz" else "uz"
        return dict(lang=lang, other=other, t=T[lang], cfg=CFG, products=products, cats=cats,
                    series=series_cards, url=lambda pth="": url(lang, pth), path=path,
                    alt_url=url(other, path), self_url=url(lang, path), site=CFG["site_url"], **extra)

    sitemap = []
    for lang in LANGS:
        for path, tpl, extra in pages:
            html = env.get_template(tpl).render(**ctx(lang, path, extra))
            out = DIST / url(lang, path).lstrip("/") / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(html, encoding="utf-8")
            sitemap.append(CFG["site_url"] + url(lang, path))
    (DIST / "404.html").write_text(env.get_template("404.html").render(**ctx("uz", "", {"page": "404"})),
                                   encoding="utf-8")
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in sitemap) + "</urlset>\n", encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {CFG['site_url']}/sitemap.xml\n",
                                     encoding="utf-8")
    print(f"built {len(sitemap)} pages, {len(products)} products -> {DIST}")


if __name__ == "__main__":
    render_all()
