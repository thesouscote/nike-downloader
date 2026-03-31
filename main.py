from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import re
import io
import zipfile
import time

app = Flask(__name__)
CORS(app)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Referer": "https://www.nike.com/",
}

NIKE_CDN          = "https://static.nike.com/a/images/"
TRANSFORM_PRIMARY  = "fl_original/f_auto,q_auto:best"
TRANSFORM_FALLBACK = "c_limit,w_5000/f_auto,q_auto:best"
MIN_FILE_SIZE      = 50 * 1024  # 50 KB

UUID_RE = re.compile(r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})")

SKIP_PATHS = {"/icons/", "/logos/", "/swoosh/", "/badge/", "/category/", "/banners/"}
SMALL_PRESETS = {
    "t_PDP_36", "t_PDP_48", "t_PDP_72", "t_PDP_144", "t_PDP_144_v1",
    "t_PDP_36_v1", "t_PDP_48_v1", "t_PDP_72_v1",
    "w_24", "w_36", "w_48", "w_72", "w_100", "t_card_v1", "t_swatch",
}

EXT_MAP = {
    "image/jpeg": ".jpg", "image/png": ".png",
    "image/webp": ".webp", "image/avif": ".avif",
}


def extract_style_color(url):
    m = re.search(r"/([A-Z]{2}\d{4}-\d{3})", url)
    return m.group(1) if m else "nike_product"


def is_obviously_small(url):
    for p in SKIP_PATHS:
        if p in url:
            return True
    for p in SMALL_PRESETS:
        if p in url:
            return True
    return False


def check_size(url):
    try:
        r = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
        if r.status_code not in (200, 206):
            return 0, False
        cl = r.headers.get("Content-Length")
        if cl is None:
            return -1, True
        size = int(cl)
        return size, size >= MIN_FILE_SIZE
    except Exception:
        return -1, True


def parse_page(page_url):
    r = requests.get(page_url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    html = r.text

    raw = re.findall(r"https://static\.nike\.com/a/images/[^\s\"'<>\\]+", html)

    seen, candidates = set(), []
    for u in raw:
        if is_obviously_small(u):
            continue
        m = UUID_RE.search(u)
        if not m:
            continue
        uuid = m.group(1)
        if uuid in seen:
            continue
        seen.add(uuid)
        fm = re.search(r"/([^/]+\.(?:png|jpg|jpeg|webp|avif))$", u, re.I)
        fname = fm.group(1) if fm else "product.png"
        candidates.append({"uuid": uuid, "filename": fname, "source": u})

    images = []
    for img in candidates:
        size, keep = check_size(img["source"])
        if keep:
            img["known_size"] = size
            images.append(img)
        time.sleep(0.05)

    return images


def build_urls(img):
    uuid  = img["uuid"]
    fname = img["filename"]
    return [
        f"{NIKE_CDN}{TRANSFORM_PRIMARY}/{uuid}/{fname}",
        f"{NIKE_CDN}{TRANSFORM_FALLBACK}/{uuid}/{fname}",
        img["source"],
    ]


def fetch_image_bytes(img):
    for url in build_urls(img):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code in (403, 404, 410):
                continue
            r.raise_for_status()
            ct  = r.headers.get("Content-Type", "image/png").split(";")[0].strip()
            ext = EXT_MAP.get(ct, ".png")
            return r.content, ext
        except Exception:
            continue
    return None, None


# ── Routes ────────────────────────────────────────────────

@app.route("/api/scan", methods=["POST"])
def scan():
    """Scanne la page Nike et retourne la liste des images trouvées."""
    data = request.json or {}
    url  = data.get("url", "").strip()

    if not url or "nike.com" not in url:
        return jsonify({"error": "URL Nike invalide"}), 400

    try:
        images = parse_page(url)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    style_color = extract_style_color(url)

    return jsonify({
        "style_color": style_color,
        "count": len(images),
        "images": [
            {
                "uuid":     img["uuid"],
                "filename": img["filename"],
                "preview":  img["source"],
                "download": build_urls(img)[0],
            }
            for img in images
        ],
    })


@app.route("/api/download", methods=["POST"])
def download():
    """Télécharge toutes les images et les retourne dans un ZIP."""
    data        = request.json or {}
    url         = data.get("url", "").strip()
    style_color = data.get("style_color", "nike_product")

    if not url or "nike.com" not in url:
        return jsonify({"error": "URL Nike invalide"}), 400

    try:
        images = parse_page(url)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not images:
        return jsonify({"error": "Aucune image trouvée"}), 404

    # Créer le ZIP en mémoire
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, img in enumerate(images, 1):
            data_bytes, ext = fetch_image_bytes(img)
            if data_bytes:
                fname = f"nike_{i:02d}_{img['uuid'][:8]}{ext}"
                zf.writestr(fname, data_bytes)

    zip_buffer.seek(0)
    zip_name = f"nike_{style_color}.zip"

    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=zip_name,
    )


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Nike Image Downloader API"})


if __name__ == "__main__":
    app.run(debug=False, port=8000)
