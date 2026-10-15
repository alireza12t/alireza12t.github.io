"""
Static checks for the website, run by release.sh and CI before anything ships.

Everything is checked against the files git tracks, because GitHub Pages is
case-sensitive and only serves what's committed (macOS is neither).
No browser and no third-party packages: stdlib + pytest only.
"""

import json
import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Internal tooling pages that are not part of the public site
SKIP_DIRS = ("resume/", ".run-tools/", "lambda/", "scripts/", ".github/", "tests/")


def _tracked_files():
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout
    # Files added in the working tree but not committed yet count too (pre-commit runs)
    extra = subprocess.run(
        ["git", "ls-files", "-z", "--others", "--exclude-standard"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return {p for p in (out + extra).split("\0") if p}


TRACKED = _tracked_files()
PAGES = sorted(p for p in TRACKED if p.endswith(".html") and not p.startswith(SKIP_DIRS))


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.refs = []          # (attr, value, tag)
        self.imgs = []          # attrs dicts
        self.html_attrs = {}
        self.has_title = False
        self.metas = []
        self.blank_links = []   # <a target=_blank> attrs
        self._in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "a" and "name" in a:
            self.ids.add(a["name"])
        if tag == "html":
            self.html_attrs = a
        if tag == "title":
            self.has_title = True
            self._in_title = True
        if tag == "meta":
            self.metas.append(a)
        if tag == "img":
            self.imgs.append(a)
        if tag == "a" and a.get("target") == "_blank":
            self.blank_links.append(a)
        for attr in ("href", "src", "poster"):
            if a.get(attr):
                self.refs.append((attr, a[attr], tag))
        if a.get("srcset"):
            for part in a["srcset"].split(","):
                url = part.strip().split(" ")[0]
                if url:
                    self.refs.append(("srcset", url, tag))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


_parsed = {}


def parse(page):
    if page not in _parsed:
        p = _PageParser()
        p.feed((ROOT / page).read_text(encoding="utf-8"))
        _parsed[page] = p
    return _parsed[page]


def _is_local(url):
    s = urlsplit(url)
    return not s.scheme and not s.netloc and not url.startswith(("//", "data:", "javascript:"))


def _resolve(page, url):
    """Map a local URL on `page` to (repo path or None, fragment)."""
    s = urlsplit(url)
    path, frag = unquote(s.path), s.fragment
    if not path:
        return page, frag
    base = Path(page).parent
    target = (Path("/") / path) if path.startswith("/") else (Path("/") / base / path)
    target = Path(*target.resolve().parts[1:]) if len(target.resolve().parts) > 1 else Path("")
    t = str(target).replace("\\", "/")
    if t in ("", "."):
        return ("index.html" if "index.html" in TRACKED else None), frag
    if t in TRACKED:
        return t, frag
    # Directory URL → its index.html (GitHub Pages behaviour)
    if f"{t}/index.html" in TRACKED:
        return f"{t}/index.html", frag
    return None, frag


def _ids_from_script(page):
    """Anchors a page makes work in JS: ids that script.js renders, and
    hashes the page's own script checks (e.g. location.hash === '#trips')."""
    ids = set()
    if "script.js" in TRACKED:
        ids |= set(re.findall(r'id="([\w-]+)"', (ROOT / "script.js").read_text(encoding="utf-8")))
    ids |= set(re.findall(r"""['"]#([\w-]+)['"]""", (ROOT / page).read_text(encoding="utf-8")))
    return ids


# ── Every page ────────────────────────────────────────────────────────────────

def test_found_pages():
    assert "index.html" in PAGES
    assert len(PAGES) >= 10


@pytest.mark.parametrize("page", PAGES)
def test_page_basics(page):
    p = parse(page)
    assert p.has_title and p.title.strip(), "missing <title>"
    assert p.html_attrs.get("lang"), "missing <html lang>"
    assert any(m.get("name") == "viewport" for m in p.metas), "missing viewport meta (breaks mobile)"
    assert any("charset" in m for m in p.metas), "missing <meta charset>"


@pytest.mark.parametrize("page", PAGES)
def test_local_links_and_assets_exist(page):
    p = parse(page)
    broken = []
    for attr, url, tag in p.refs:
        if not _is_local(url) or url.startswith(("mailto:", "tel:", "#")) and attr != "href":
            continue
        if url.startswith(("mailto:", "tel:", "sms:")):
            continue
        target, _ = _resolve(page, url)
        if target is None:
            broken.append(f"<{tag} {attr}={url!r}>")
    assert not broken, "broken local references (not in git):\n  " + "\n  ".join(broken)


@pytest.mark.parametrize("page", PAGES)
def test_anchors_exist(page):
    p = parse(page)
    missing = []
    for attr, url, tag in p.refs:
        if attr != "href" or not _is_local(url) or url.startswith(("mailto:", "tel:")):
            continue
        target, frag = _resolve(page, url)
        if not frag or target is None or not target.endswith(".html"):
            continue
        if frag in parse(target).ids or frag in _ids_from_script(target):
            continue
        missing.append(url)
    assert not missing, "links to #anchors that don't exist:\n  " + "\n  ".join(missing)


@pytest.mark.parametrize("page", PAGES)
def test_images_have_alt(page):
    missing = [i.get("src", "?") for i in parse(page).imgs if "alt" not in i]
    assert not missing, "images without an alt attribute:\n  " + "\n  ".join(missing)


@pytest.mark.parametrize("page", PAGES)
def test_external_blank_links_are_safe(page):
    bad = [a.get("href") for a in parse(page).blank_links
           if not _is_local(a.get("href", "")) and "noopener" not in (a.get("rel") or "")
           and "noreferrer" not in (a.get("rel") or "")]
    # Modern browsers imply noopener, so this is a warning-level check kept strict for new pages
    assert not bad, 'target="_blank" links without rel="noopener":\n  ' + "\n  ".join(bad)


@pytest.mark.parametrize("page", PAGES)
def test_no_duplicate_ids(page):
    text = (ROOT / page).read_text(encoding="utf-8")
    ids = re.findall(r'\sid="([^"]+)"', text)
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    assert not dupes, f"duplicate ids: {dupes}"


# ── Data and scripts ─────────────────────────────────────────────────────────

JSON_FILES = sorted(p for p in TRACKED if p.endswith(".json") and not p.startswith(SKIP_DIRS))


@pytest.mark.parametrize("path", JSON_FILES)
def test_json_is_valid(path):
    json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_availabilities_shape():
    d = json.loads((ROOT / "availabilities.json").read_text(encoding="utf-8"))
    for key in ("timezone", "meetingDurationMinutes", "weeklyAvailability", "blockedSlots", "maxBookingDaysAhead"):
        assert key in d, f"availabilities.json missing {key}"
    days = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
    assert set(d["weeklyAvailability"]) == days
    hhmm = re.compile(r"^\d\d:\d\d$")
    for day, ranges in d["weeklyAvailability"].items():
        for r in ranges:
            assert hhmm.match(r["start"]) and hhmm.match(r["end"]), f"{day}: bad time {r}"
            assert r["start"] < r["end"], f"{day}: start after end {r}"


JS_FILES = sorted(p for p in TRACKED if p.endswith(".js") and not p.startswith(SKIP_DIRS))


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
@pytest.mark.parametrize("path", JS_FILES)
def test_js_syntax(path):
    r = subprocess.run(["node", "--check", str(ROOT / path)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


# ── Translations (EN / FR / FA on the main site) ─────────────────────────────

def _translation_keys():
    src = (ROOT / "script.js").read_text(encoding="utf-8")
    block = src[src.index("const translations = {"): src.index("\n};", src.index("const translations = {"))]
    langs = {}
    for m in re.finditer(r"^    (\w\w): \{\n(.*?)^    \},?$", block, re.S | re.M):
        # Keys may share a line: "cal_sun: 'Sun', cal_mon: 'Mon',"
        langs[m.group(1)] = set(re.findall(r"(?:^\s+|,\s*)(\w+):\s*['\"`]", m.group(2), re.M))
    return langs


def test_every_language_has_the_same_keys():
    langs = _translation_keys()
    assert set(langs) == {"en", "fr", "fa"}, f"languages found: {sorted(langs)}"
    en = langs["en"]
    for lang, keys in langs.items():
        assert keys == en, f"{lang}: missing {sorted(en - keys)}, extra {sorted(keys - en)}"


def test_every_i18n_key_used_in_html_is_defined():
    en = _translation_keys()["en"]
    used = {}
    for page in PAGES:
        for key in re.findall(r'data-i18n(?:-html)?="(\w+)"', (ROOT / page).read_text(encoding="utf-8")):
            used.setdefault(key, page)
    missing = {k: p for k, p in used.items() if k not in en}
    assert not missing, f"data-i18n keys with no translation: {missing}"


# ── Apps section ─────────────────────────────────────────────────────────────

def _apps_block():
    src = (ROOT / "script.js").read_text(encoding="utf-8")
    start = src.index("const APPS = [")
    return src[start: src.index("\n];", start)]


def test_apps_assets_exist():
    block = _apps_block()
    paths = re.findall(r"'(images/[^']+)'", block)
    assert paths, "no image paths found in APPS"
    missing = [p for p in paths if p not in TRACKED]
    assert not missing, f"APPS references images not in git: {missing}"


def test_apps_have_required_fields():
    block = _apps_block()
    apps = re.split(r"\n    \{", block)[1:]
    assert apps, "APPS is empty"
    for app in apps:
        name = re.search(r"name: '([^']+)'", app)
        assert name, f"app without a name:\n{app[:120]}"
        for field in ("pitch", "platforms", "accent", "appStore"):
            assert re.search(rf"\b{field}:", app), f"{name.group(1)}: missing {field}"
        assert re.search(r"appStore: 'https://apps\.apple\.com/", app), f"{name.group(1)}: appStore must be an App Store URL"
    assert sum("featured: true" in a for a in apps) <= 1, "only one app can be featured"


def test_apps_screenshot_sizes_match_files():
    """Declared w/h must match the real image, or the page jumps while loading."""
    block = _apps_block()
    for src, w, h in re.findall(r"src: '([^']+)', w: (\d+), h: (\d+)", block):
        real = _image_size(ROOT / src)
        if real is None:
            continue
        assert real == (int(w), int(h)), f"{src}: declared {w}x{h}, file is {real[0]}x{real[1]}"


def _image_size(path):
    """Width/height for WebP (VP8/VP8L/VP8X) without Pillow."""
    data = path.read_bytes()[:64]
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    chunk = data[12:16]
    if chunk == b"VP8X":
        return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
    if chunk == b"VP8 ":
        return int.from_bytes(data[26:28], "little") & 0x3FFF, int.from_bytes(data[28:30], "little") & 0x3FFF
    if chunk == b"VP8L":
        b = int.from_bytes(data[21:25], "little")
        return (b & 0x3FFF) + 1, ((b >> 14) & 0x3FFF) + 1
    return None


@pytest.mark.parametrize("page", PAGES)
def test_img_sizes_match_files(page):
    """width/height on <img> must match the real WebP, or the page jumps while loading."""
    wrong = []
    for img in parse(page).imgs:
        src, w, h = img.get("src", ""), img.get("width"), img.get("height")
        if not (w and h and _is_local(src) and src.endswith(".webp")):
            continue
        target, _ = _resolve(page, src)
        if target is None:
            continue
        real = _image_size(ROOT / target)
        if real and real != (int(w), int(h)) and abs(real[0] / real[1] - int(w) / int(h)) > 0.002:
            wrong.append(f"{src}: declared {w}x{h}, file is {real[0]}x{real[1]}")
    assert not wrong, "\n  ".join(["image sizes don't match:"] + wrong)


# ── Regressions ──────────────────────────────────────────────────────────────

def test_personal_trips_hash_respects_hidden_tab():
    """/personal/#trips (the Spain page's back link) must not open the hidden Trips panel."""
    src = (ROOT / "personal/index.html").read_text(encoding="utf-8")
    trips_hidden = re.search(r"""<button[^>]*showTab\('trips'[^>]*style="display:none\"""", src)
    if trips_hidden:
        assert "location.hash === '#trips' &&" in src and "style.display !== 'none'" in src, \
            "#trips handler opens the hidden Trips tab, which shows a blank page"
