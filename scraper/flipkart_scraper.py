"""
scraper/flipkart_scraper.py
Paginated Selenium-based Flipkart review scraper.

Flipkart layout variants (checked 2025):
  Layout A (gMdEY7 — most products):
    - Review card  : div.gMdEY7
    - Review body  : div.G4PxIA  (truncated; READ MORE span removed)
    - Review title : p.qW2QI1
    - Per-review rating : div.MKiFS6  (first char = star digit)

  Layout B (vQDoqR — some product categories):
    - Review card  : div.vQDoqR
    - Review text  : <a> with class '_1o6mltljo'
    - Per-review rating : div._7dzyg26

Old selectors (ZmyHeo, RcXBOT, z9E0IG, etc.) all return 0 on current pages.
"""
import re
import time
import os
import shutil
from bs4 import BeautifulSoup


# ── Old-layout selectors kept as final fallback ───────────────────────────────
_OLD_SELECTORS = [
    "div.ZmyHeo", "div.RcXBOT", "div.z9E0IG", "p.z9E0IG",
    "div._11pzQk", "div.t-ZTKy", "div._2-N8zT", "div.col.EPCmJX.Ma1fCG",
]

NOT_FOUND_PHRASES = [
    "page you are looking for has been moved",
    "page not found", "has been moved or deleted",
    "unfortunately", "go to homepage",
]

SKIP_PHRASES = {
    "sign in", "add to cart", "wishlist", "sort by", "filter",
    "helpful", "report abuse", "certified buyer", "flipkart assured",
    "seller", "exchange offer", "delivery", "customer care",
    "moved or deleted", "go to homepage", "unfortunately",
    "ratings and reviews", "read all reviews", "was this review",
    "rate this product", "select a reason", "know more",
}


# ── Driver helpers ────────────────────────────────────────────────────────────

def _find_chromedriver():
    # Check env var first (set in Docker/production)
    env_cd = os.environ.get("CHROMEDRIVER_BIN")
    if env_cd and os.path.isfile(env_cd) and "/snap/" not in env_cd:
        return env_cd
    # webdriver-manager first — downloads the exact matching version
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        p = ChromeDriverManager().install()
        if p and "/snap/" not in p:
            return p
    except Exception:
        pass
    # Non-snap system paths
    for p in ("/usr/bin/chromedriver", "/usr/lib/chromium/chromedriver",
              "/usr/lib/chromium-browser/chromedriver"):
        if os.path.isfile(p) and "/snap/" not in p:
            return p
    return None


def _find_chrome_binary():
    env_cb = os.environ.get("CHROME_BIN")
    if env_cb and os.path.isfile(env_cb) and "/snap/" not in env_cb:
        return env_cb
    # Prefer real Google Chrome over Snap Chromium
    for p in ("/usr/bin/google-chrome", "/usr/bin/google-chrome-stable",
              "/usr/bin/chromium-browser", "/usr/bin/chromium"):
        if os.path.isfile(p) and "/snap/" not in p:
            return p
    return None


def get_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,900")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-images")
    opts.add_argument("--blink-settings=imagesEnabled=false")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    # Set Chrome binary if found (needed for Chromium on Linux servers)
    cb = _find_chrome_binary()
    if cb:
        opts.binary_location = cb

    cd = _find_chromedriver()
    driver = (webdriver.Chrome(service=Service(cd), options=opts)
              if cd else webdriver.Chrome(options=opts))
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
    })
    return driver


# ── URL helpers ───────────────────────────────────────────────────────────────

def _get_base_reviews_url(url):
    """Return (primary_base_url, [fallback_urls]) for paginated scraping."""
    pid_m = re.search(r'[?&]pid=([A-Z0-9]+)', url, re.I)
    pid   = pid_m.group(1) if pid_m else None
    itm_m = re.search(r'/(itm[^/?]+)', url, re.I)
    itm   = itm_m.group(1) if itm_m else None

    # ── Case 1: URL is already a reviews page (/product-reviews/ in path) ────
    # Use it directly — just strip the &lid= noise so pagination appends cleanly
    path = url.split('?')[0]
    if '/product-reviews/' in path or path.endswith('/product-reviews'):
        clean = re.sub(r'[?&]lid=[^&]*', '', url)   # strip lid=...
        clean = re.sub(r'\?&', '?', clean)            # fix ?& → ?
        clean = clean.rstrip('?&')
        return clean, []

    # ── Case 2: URL is a product page — build the reviews URL ────────────────
    slug_m    = re.search(r'flipkart\.com/([^?#]+)', url)
    slug      = slug_m.group(1).rstrip('/') if slug_m else None
    base_slug = re.sub(r'/p/[^/]+$', '', slug) if slug else None

    base = None
    fallbacks = []

    # NEW format (2025): slug/product-reviews/itm_id?pid=PID&marketplace=FLIPKART
    if base_slug and pid and itm:
        base = (f"https://www.flipkart.com/{base_slug}/product-reviews/{itm}"
                f"?pid={pid}&marketplace=FLIPKART")

    # OLD format: slug/product-reviews?pid=PID
    if base_slug and pid:
        fallbacks.append(f"https://www.flipkart.com/{base_slug}/product-reviews"
                         f"?pid={pid}&marketplace=FLIPKART")

    # Legacy /product-reviews/PID and /product-reviews/itm...
    if pid:
        fallbacks.append(f"https://www.flipkart.com/product-reviews/{pid}")
    if itm:
        fallbacks.append(f"https://www.flipkart.com/product-reviews/{itm}")

    # Final fallback: original product URL (embeds a few reviews)
    fallbacks.append(url)
    return base, fallbacks


# ── Text helpers ──────────────────────────────────────────────────────────────

def _is_404(soup):
    txt = soup.get_text(" ", strip=True).lower()
    # Require at least 1000 chars (not 3000) to avoid false-negatives on slow loads
    return len(txt) < 1000 or any(p in txt for p in NOT_FOUND_PHRASES)


def _clean(txt):
    txt = re.sub(r'READ MORE', '', txt, flags=re.I)
    txt = re.sub(r'\.{3}\s*more\s*$', '', txt, flags=re.I)  # strip "...more" truncation
    return re.sub(r'\s+', ' ', txt).strip()


def _is_junk(txt):
    low = txt.lower().strip()
    if re.match(r'^[\d\s★,.]+$', txt):
        return True
    if re.match(r'^\d', txt) or txt.startswith('₹'):
        return True
    if 'flipkart.com' in low or 'price in india' in low:
        return True
    if 'private limited' in low or 'mail us:' in low or 'registered office' in low:
        return True
    if len(re.findall(r'[a-zA-Z]{3,}', txt)) < 3:
        return True
    # Use word-boundary matching so "Road," still matches "road"
    addr = {'road', 'street', 'lane', 'colony', 'district', 'village',
            'nagar', 'sector'}
    if any(re.search(r'\b' + w + r'\b', low) for w in addr):
        return True
    return False


# ── Core review extraction ────────────────────────────────────────────────────

def _extract_from_gmdey7_cards(soup):
    """
    Layout A (most Flipkart products, 2025): each review is a div.gMdEY7.
      - Rating : div.MKiFS6  (first char = digit 1-5)
      - Title  : p.qW2QI1
      - Body   : div.G4PxIA  (READ MORE span stripped)
    Returns list of {"text": str, "rating": int|None}.
    """
    cards = soup.select("div.gMdEY7")
    if not cards:
        return []

    results = []
    seen = set()

    for card in cards:
        # ── Rating ────────────────────────────────────────────────────────────
        rating = None
        rating_div = card.select_one("div.MKiFS6")
        if rating_div:
            try:
                v = int(rating_div.get_text(strip=True)[0])
                if 1 <= v <= 5:
                    rating = v
            except (ValueError, IndexError):
                pass

        # ── Title ─────────────────────────────────────────────────────────────
        title = ""
        title_tag = card.select_one("p.qW2QI1")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # ── Body ──────────────────────────────────────────────────────────────
        body = ""
        body_tag = card.select_one("div.G4PxIA")
        if body_tag:
            for span in body_tag.select("span.kXosBy"):
                span.decompose()
            body = _clean(body_tag.get_text(" ", strip=True))

        # Combine title + body
        if title and body:
            review_text = f"{title}. {body}"
        elif body:
            review_text = body
        elif title:
            review_text = title
        else:
            continue

        if review_text in seen or _is_junk(review_text):
            continue

        seen.add(review_text)
        results.append({"text": review_text, "rating": rating})

    return results


def _extract_from_vqdoqr_cards(soup):
    """
    Layout B (some Flipkart product categories, 2025): each review is a div.vQDoqR.
      - Review text  : <a> with class '_1o6mltljo'
      - Per-review rating : div._7dzyg26
    Returns list of {"text": str, "rating": int|None}.
    """
    cards = soup.select("div.vQDoqR")
    if not cards:
        return []

    results = []
    seen = set()

    for card in cards:
        # ── Review text ───────────────────────────────────────────────────────
        review_text = None

        for a in card.find_all("a"):
            if "_1o6mltljo" in a.get("class", []):
                txt = _clean(a.get_text(" ", strip=True))
                if len(txt) >= 5:
                    review_text = txt
                    break

        if not review_text:
            for div in card.find_all("div"):
                if "v1zwn26" in div.get("class", []):
                    txt = _clean(div.get_text(" ", strip=True))
                    if len(txt) >= 5:
                        review_text = txt
                        break

        if not review_text or review_text in seen:
            continue

        # ── Rating ────────────────────────────────────────────────────────────
        rating = None
        for div in card.find_all("div"):
            cls = div.get("class", [])
            if "_7dzyg26" in cls or "css-146c3p1" in cls or "_1lRcqv" in cls:
                try:
                    v = int(div.get_text(strip=True))
                    if 1 <= v <= 5:
                        rating = v
                        break
                except ValueError:
                    pass

        # Filter noise cards
        low_rt = review_text.lower()
        if ('₹' in review_text
                or review_text.startswith('AD ')
                or review_text.startswith('Review for:')
                or re.match(r'^[\d\s★,.]+$', review_text)
                or re.match(r'^\d+\.?\d*\s', review_text)
                or re.search(r'\b(Bronze|Silver|Gold|Platinum)\b.*\bReviewer\b', review_text)
                or re.search(r'\bReviewer\b', review_text)
                or ('flipkart' in low_rt and 'shopping' in low_rt)
                or re.match(r'^(Overall|Camera|Battery|Display|Design|Performance)', review_text)
                or (rating is None and len(review_text) < 25)):
            continue

        seen.add(review_text)
        results.append({"text": review_text, "rating": rating})

    return results


def _extract_rnw_layout(soup):
    """
    Layout C — Flipkart React Native Web (RNW) rendering (2025).
    Body text lives in span.css-1jxf684.
    The grandparent (span → div.css-146c3p1 → div.css-g5y9jx) holds the
    full review blob: "{rating} • {title} Review for: {variant} {body} {reviewer} …"

    Returns list of {"text": str, "rating": int|None}.
    """
    body_spans = soup.select("span.css-1jxf684")
    if not body_spans:
        return []

    results = []
    seen = set()

    for span in body_spans:
        body = span.get_text(strip=True)
        if not body or len(body) < 5:
            continue

        # Walk up to find the container that has the rating prefix "N.N •"
        # Truncated reviews: 2 levels up; expanded (READ MORE) reviews: 3 levels up
        container = None
        try:
            node = span.parent  # div.css-146c3p1
            for _ in range(4):
                node = node.parent
                txt = node.get_text(" ", strip=True)
                if re.match(r"^\d+\.?\d*\s*[•·]", txt):
                    container = node
                    break
        except AttributeError:
            pass
        if container is None:
            # No rating-prefixed container found — skip (avoids nav/title text)
            continue

        full_text = container.get_text(" ", strip=True)

        # ── Rating ─────────────────────────────────────────────────────────
        rating = None
        m = re.match(r"^(\d+\.?\d*)\s*[•·]", full_text)
        if m:
            try:
                v = round(float(m.group(1)))
                if 1 <= v <= 5:
                    rating = v
            except (ValueError, TypeError):
                pass

        # ── Title (between first bullet and "Review for:" or body start) ──
        title = ""
        body_anchor = re.escape(body[:25])
        tm = re.search(r"[•·]\s*(.+?)\s*(?:Review for:|" + body_anchor + r")",
                       full_text)
        if tm:
            title = tm.group(1).strip()
        # Guard: if title IS the body (no separate title), skip title
        if title and title.lower() == body.lower():
            title = ""

        full_review = f"{title}. {body}" if title else body
        full_review = _clean(full_review)

        if not full_review or full_review in seen or _is_junk(full_review):
            continue

        seen.add(full_review)
        results.append({"text": full_review, "rating": rating})

    return results


def _extract_from_cards(soup):
    """
    Try all known Flipkart layouts in order:
      A: div.gMdEY7     (most products, classic 2025 layout)
      B: div.vQDoqR     (some product categories, 2025)
      C: span.css-1jxf684  (React Native Web rendering, 2025)
    """
    results = _extract_from_gmdey7_cards(soup)
    if not results:
        results = _extract_from_vqdoqr_cards(soup)
    if not results:
        results = _extract_rnw_layout(soup)
    return results


def _extract_reviews_legacy(soup):
    """Old-layout fallback — returns list of {"text": str, "rating": None} dicts."""
    reviews, seen = [], set()

    # Old CSS selectors
    for sel in _OLD_SELECTORS:
        for node in soup.select(sel):
            txt = _clean(node.get_text(" ", strip=True))
            if len(txt) > 40 and txt not in seen and not _is_junk(txt):
                reviews.append({"text": txt, "rating": None})
                seen.add(txt)
        if reviews:
            return reviews

    # Structural heuristic
    for tag in soup.find_all(["div", "p", "span"]):
        if len([c for c in tag.children if hasattr(c, 'get_text')]) > 4:
            continue
        txt = _clean(tag.get_text(" ", strip=True))
        low = txt.lower()
        if (40 < len(txt) < 800
                and txt not in seen
                and not any(s in low for s in SKIP_PHRASES)
                and not _is_junk(txt)):
            reviews.append({"text": txt, "rating": None})
            seen.add(txt)
        if len(reviews) >= 50:
            break

    return reviews


_NOISE_PATTERNS = [
    re.compile(r'\bReviewer\b'),                              # reviewer profile cards
    re.compile(r'\b(Bronze|Silver|Gold|Platinum)\b'),         # reviewer tier labels
    re.compile(r'^Review for:', re.I),                        # product variant info
    re.compile(r'^(Overall|Camera|Battery|Display|Design|Performance)\b'),
    re.compile(r'flipkart.*shopping', re.I),                  # nav bar text
    re.compile(r'^[\d\s★,.]+$'),                              # pure numbers/stars
    re.compile(r'^\d+\.?\d*\s+[A-Z]'),                       # "4.7 Apple iPhone..."
]

def _is_noise(text: str) -> bool:
    """Return True if text is clearly not a genuine review."""
    if '₹' in text:
        return True
    if text.startswith('AD '):
        return True
    for pat in _NOISE_PATTERNS:
        if pat.search(text):
            return True
    # Must have at least 4 real words of 3+ chars (catches "vaddadi sai vigyan...")
    # Unless it's a longer genuine review
    real_words = re.findall(r'[a-zA-Z]{3,}', text)
    if len(real_words) < 3 and len(text) < 40:
        return True
    return False


def _extract_reviews(soup):
    """
    Try new card layout first, fall back to old selectors.
    Always returns list of {"text": str, "rating": int|None} dicts.
    Noise is filtered in a final pass.
    """
    results = _extract_from_cards(soup)
    if not results:
        results = _extract_reviews_legacy(soup)
    # Final noise filter — catches anything that slipped through per-card filters
    return [r for r in results if not _is_noise(r["text"])]


# ── Page loader ───────────────────────────────────────────────────────────────

def _load_page(driver, url, fast=False):
    """
    Load URL, wait for review content to appear, scroll, return soup.
    fast=True (pages 2+): shorter timeout, no READ MORE expansion.
    Returns soup or None.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    driver.get(url)

    # Wait up to N seconds for a review element to appear — return early if found
    timeout = 5 if fast else 8
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "span.css-1jxf684, div.gMdEY7, div.vQDoqR")
            )
        )
    except Exception:
        pass  # timed out — proceed with whatever is loaded

    # Two-step scroll: enough to trigger lazy content
    for pct in ([0.6, 1.0] if fast else [0.3, 0.6, 1.0]):
        driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {pct});")
        time.sleep(0.3)

    # Expand READ MORE on slow (page-1) loads only
    if not fast:
        for xpath in [
            "//a[contains(text(),'READ MORE')]",
            "//span[contains(text(),'READ MORE')]",
        ]:
            for btn in driver.find_elements(By.XPATH, xpath):
                try:
                    driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.1)
                except Exception:
                    pass

    soup = BeautifulSoup(driver.page_source, "html.parser")
    return None if _is_404(soup) else soup


# ── Public API ────────────────────────────────────────────────────────────────

_REVIEWS_PER_PAGE    = 10   # Flipkart shows 10 reviews per page
_DEFAULT_MAX_PAGES   = 50   # default cap: ~300-400 reviews in 4-5 min
_MAX_PAGES_HARD_CAP  = 120  # absolute ceiling when caller sets max_pages explicitly



def _detect_total_reviews(soup) -> int | None:
    """
    Parse the total review count shown on the reviews page
    (e.g. '966 Ratings & 109 Reviews' or '1,096 reviews').
    Returns int or None if not found.
    """
    page_text = soup.get_text(" ", strip=True)
    # Pattern: "1,096 Reviews" or "109 Reviews" (with optional comma-separated thousands)
    for pat in [
        r'([\d,]+)\s+[Rr]eviews',
        r'[Rr]atings\s*[&and]+\s*([\d,]+)\s*[Rr]eviews',
        r'([\d,]+)\s+[Rr]atings\s*[&and]+',
    ]:
        m = re.search(pat, page_text)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                pass
    return None


def scrape(url, max_pages=None):
    """
    Scrape a Flipkart product URL.

    max_pages: if None (default), auto-detect total review count from page 1
               and compute the exact number of pages needed (capped at
               _MAX_PAGES_HARD_CAP=120 ≈ 1200 reviews).
               Pass an explicit int to override.

    Returns dict:
      {
        "title":    str | None,
        "rating":   float | None,          # overall product star rating
        "images":   [str],
        "reviews":  [{"text": str, "rating": int|None}],
        "error":    str | None,
      }
    """
    result = {"title": None, "rating": None, "images": [], "reviews": [], "error": None}
    driver = None
    try:
        driver = get_driver()

        # ── Product page ──────────────────────────────────────────────────────
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Title
        for sel in ["span.B_NuCI", "span.VU-ZEz", "h1.yhB1nd", "h1[class]", "h1"]:
            node = soup.select_one(sel)
            if node:
                result["title"] = node.get_text(strip=True)
                break
        if not result["title"]:
            og = soup.find("meta", property="og:title")
            if og:
                raw = og.get("content", "").strip()
                # Strip " Reviews: Latest Review of … | Price in India | Flipkart.com"
                raw = re.sub(r'\s*Reviews:.*$', '', raw, flags=re.I | re.S).strip()
                raw = re.sub(r'\s*\|\s*Price in India.*$', '', raw, flags=re.I).strip()
                raw = re.sub(r'\s*\|\s*Flipkart\.com\s*$', '', raw, flags=re.I).strip()
                result["title"] = raw if raw else None

        # Overall product rating
        def _rating(s):
            # 1. Known CSS selectors for the overall rating widget
            for sel in ["div._3LWZlK", "div.XQDdHH", "div.CxhGGd", "span._1lRcqv",
                        "div.IHXGEy"]:
                n = s.select_one(sel)
                if n:
                    try:
                        v = float(n.text.strip())
                        if 1.0 <= v <= 5.0:
                            return v
                    except Exception:
                        pass
            # 2. Regex near context keywords (require "ratings" or "reviews" nearby)
            page_text = s.get_text(" ", strip=True)
            for pat in [
                r'([1-5]\.\d)\s*(?:out of 5|/5)',
                r'([1-5]\.\d)\s*★\s*[\d,]+\s*[Rr]atings',
                r'([1-5]\.\d)\s*[\d,]+\s*(?:ratings|reviews)',
            ]:
                m = re.search(pat, page_text, re.I)
                if m:
                    try:
                        v = float(m.group(1))
                        if 1.0 <= v <= 5.0:
                            return v
                    except Exception:
                        pass
            return None

        result["rating"] = _rating(soup)

        # Images
        for sel in ["img._396cs4", "img.DByuf4", "img.q6DClP",
                    "div[class*='image'] img", "div[class*='media'] img"]:
            imgs = soup.select(sel)
            if imgs:
                result["images"] = [i.get("src") for i in imgs if i.get("src")][:10]
                break
        if not result["images"]:
            for img in soup.find_all("img"):
                src = img.get("src", "")
                if src and "rukminim" in src:
                    result["images"].append(src)
                if len(result["images"]) >= 10:
                    break

        # ── Reviews with pagination ───────────────────────────────────────────
        base_url, fallbacks = _get_base_reviews_url(url)
        candidates = ([base_url] if base_url else []) + fallbacks
        working_base = None
        tried = []

        # Find a working reviews URL — save the soup to reuse for page 1
        page1_soup = None
        for candidate in candidates:
            tried.append(candidate)
            soup_candidate = _load_page(driver, candidate)
            if soup_candidate is not None:
                working_base = candidate
                page1_soup = soup_candidate   # reuse — avoids loading page 1 twice
                print(f"[scraper] Reviews URL: {candidate}")
                break
            print(f"[scraper] 404/empty: {candidate}")

        if working_base is None:
            result["error"] = (
                "All review URL formats returned 404 or empty. "
                f"Tried: {tried}"
            )
            return result

        all_reviews = []
        seen_global = set()

        # Page limit: caller override → else _DEFAULT_MAX_PAGES
        hard_limit = max_pages if max_pages is not None else _DEFAULT_MAX_PAGES
        consecutive_empty = 0
        _MAX_CONSECUTIVE_EMPTY = 2

        for page_num in range(1, _MAX_PAGES_HARD_CAP + 1):
            is_first = page_num == 1
            if is_first:
                # Reuse soup already loaded during candidate check — no extra request
                rev_soup = page1_soup
                page_url = working_base
            else:
                sep = "&" if "?" in working_base else "?"
                page_url = f"{working_base}{sep}page={page_num}"

            print(f"[scraper] Page {page_num}/{hard_limit}")

            if not is_first:
                try:
                    rev_soup = _load_page(driver, page_url, fast=True)
                except Exception as page_err:
                    print(f"[scraper] Page {page_num} → error: {page_err}, stopping")
                    result["error"] = f"Partial: stopped at page {page_num}: {page_err}"
                    break

            if rev_soup is None:
                print(f"[scraper] Page {page_num} → 404, stopping")
                break

            # Detect total review count on page 1 (for display only)
            if is_first:
                total_detected = _detect_total_reviews(rev_soup)
                if total_detected:
                    print(f"[scraper] {total_detected} total reviews on Flipkart, "
                          f"scraping up to {hard_limit} pages")

            page_reviews = _extract_reviews(rev_soup)
            new = []
            for r in page_reviews:
                norm = re.sub(r'\s+', ' ', r["text"]).strip()
                if norm not in seen_global:
                    seen_global.add(norm)
                    new.append(r)

            if not new:
                consecutive_empty += 1
                print(f"[scraper] Page {page_num} → 0 new "
                      f"({consecutive_empty}/{_MAX_CONSECUTIVE_EMPTY} empty in a row)")
                if consecutive_empty >= _MAX_CONSECUTIVE_EMPTY:
                    print("[scraper] Stopping — reviews exhausted")
                    break
            else:
                consecutive_empty = 0
                print(f"[scraper] Page {page_num} → {len(new)} new "
                      f"(total: {len(all_reviews) + len(new)})")
                all_reviews.extend(new)

            # Stop when we've hit the page limit
            if page_num >= hard_limit:
                print(f"[scraper] Reached page limit ({hard_limit}), stopping")
                break

        # Failure diagnosis (only when zero reviews collected)
        if not all_reviews:
            try:
                page_text = (BeautifulSoup(driver.page_source, "html.parser")
                             .get_text().lower())
                if any(k in page_text for k in ["robot", "captcha", "access denied"]):
                    result["error"] = "Bot/CAPTCHA wall detected. Try again later."
                elif any(k in page_text for k in ["sign in", "login to continue"]):
                    result["error"] = "Flipkart requires login to view reviews."
                elif not result["error"]:
                    diag_soup = BeautifulSoup(driver.page_source, "html.parser")
                    classes = []
                    for tag in diag_soup.find_all(["div", "span", "p"], class_=True):
                        for c in tag.get("class", []):
                            if c not in classes:
                                classes.append(c)
                    result["error"] = (
                        "Reviews page loaded but no review text found. "
                        "Flipkart may have changed CSS classes again. "
                        f"Classes found: {', '.join(classes[:30])}"
                    )
            except Exception:
                if not result["error"]:
                    result["error"] = "No reviews found."
            return result

        # Final dedup: exact-match only (preserve all unique reviews)
        reviews_final = []
        seen_final = set()
        for r in all_reviews:
            norm = re.sub(r'\s+', ' ', r["text"]).strip()
            if norm not in seen_final:
                reviews_final.append(r)
                seen_final.add(norm)

        print(f"[scraper] Total reviews collected: {len(reviews_final)}")
        result["reviews"] = reviews_final

    except Exception as e:
        result["error"] = f"Scraping error: {e}"
        import traceback; traceback.print_exc()
    finally:
        if driver:
            driver.quit()

    return result
