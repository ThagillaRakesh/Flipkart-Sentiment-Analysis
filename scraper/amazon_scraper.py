"""
scraper/amazon_scraper.py
Selenium-based Amazon India review scraper.

Extracts ASIN from any amazon.in product/reviews URL, paginates through
/product-reviews/{ASIN}?pageNumber=X, and returns the same dict shape
as the Flipkart scraper so the rest of the pipeline is unchanged.
"""

import re
import time
import os
from bs4 import BeautifulSoup

_DEFAULT_MAX_PAGES = 50
_REVIEWS_PER_PAGE  = 10

# Reuse the same Selenium driver setup from the Flipkart scraper
from scraper.flipkart_scraper import get_driver


# ── URL helpers ────────────────────────────────────────────────────────────────

def _extract_asin(url: str):
    """Extract a 10-char ASIN from any amazon.in URL."""
    m = re.search(r"/(?:dp|product-reviews|gp/product|ASIN)/([A-Z0-9]{10})", url)
    return m.group(1) if m else None


def _reviews_url(asin: str, page: int = 1) -> str:
    return (f"https://www.amazon.in/product-reviews/{asin}/"
            f"?reviewerType=all_reviews&sortBy=recent&pageNumber={page}")


# ── Extraction helpers ─────────────────────────────────────────────────────────

def _detect_total(soup) -> int:
    """Try to read total review count from the page."""
    for sel in [
        'div[data-hook="cr-filter-info-review-rating-count"]',
        'span[data-hook="total-review-count"]',
        'div#filter-info-section span',
    ]:
        el = soup.select_one(sel)
        if el:
            m = re.search(r"([\d,]+)\s*(?:global\s*)?review", el.get_text())
            if m:
                return int(m.group(1).replace(",", ""))
    return 0


def _extract_product_title(soup) -> str | None:
    """Read product title from the reviews page header."""
    for sel in [
        'a.product-title-link span',
        'a.product-title span',
        'div.product-title a',
        'h1.a-size-large span',
        'h1 span',
    ]:
        el = soup.select_one(sel)
        if el:
            t = el.get_text(strip=True)
            if len(t) > 5:
                return t
    return None


def _extract_product_rating(soup) -> str | None:
    """Read the overall product rating shown on the reviews page."""
    for sel in [
        'div[data-hook="rating-out-of-text"]',
        'span[data-hook="rating-out-of-text"]',
        'i[data-hook="average-star-rating"] span.a-icon-alt',
    ]:
        el = soup.select_one(sel)
        if el:
            m = re.search(r"(\d+\.?\d*)", el.get_text())
            if m:
                return m.group(1)
    return None


def _extract_reviews(soup) -> list:
    """Parse one reviews page; returns list of {text, rating}."""
    cards = soup.select('div[data-hook="review"]')
    if not cards:
        return []

    results = []
    seen    = set()

    for card in cards:
        # ── Rating ────────────────────────────────────────────────────────────
        rating = None
        for r_sel in [
            'i[data-hook="review-star-rating"] span.a-icon-alt',
            'i[data-hook="cmps-review-star-rating"] span.a-icon-alt',
        ]:
            r_el = card.select_one(r_sel)
            if r_el:
                rm = re.match(r"(\d+\.?\d*)", r_el.get_text(strip=True))
                if rm:
                    try:
                        v = round(float(rm.group(1)))
                        if 1 <= v <= 5:
                            rating = v
                    except ValueError:
                        pass
                break

        # ── Title ─────────────────────────────────────────────────────────────
        title = ""
        for t_sel in [
            'span[data-hook="review-title"] span:not([class])',
            'a[data-hook="review-title"] span:not([class])',
            'span[data-hook="review-title"]',
        ]:
            t_el = card.select_one(t_sel)
            if t_el:
                t = t_el.get_text(strip=True)
                # Amazon sometimes prefixes with star text, strip it
                t = re.sub(r"^\d+\.?\d*\s+out\s+of\s+\d+\s+stars?\s*", "", t, flags=re.I)
                if len(t) > 2:
                    title = t
                    break

        # ── Body ──────────────────────────────────────────────────────────────
        body = ""
        b_el = card.select_one('span[data-hook="review-body"] span')
        if b_el:
            body = re.sub(r"\s+", " ", b_el.get_text(" ", strip=True)).strip()
            body = re.sub(r"Read more\s*$", "", body, flags=re.I).strip()

        if not body:
            continue

        # Combine
        if title and title.lower() not in body.lower()[:len(title) + 5]:
            text = f"{title}. {body}"
        else:
            text = body
        text = re.sub(r"\s+", " ", text).strip()

        if len(text) < 8 or text in seen:
            continue

        seen.add(text)
        results.append({"text": text, "rating": rating})

    return results


# ── Public API ─────────────────────────────────────────────────────────────────

def scrape(url: str) -> dict:
    """
    Scrape Amazon India product reviews.

    Returns the same dict shape as flipkart_scraper.scrape():
        {
            "reviews": [{"text": str, "rating": int|None}, ...],
            "title":   str | None,
            "rating":  str | None,
            "images":  [],
            "error":   str | None,
        }
    """
    result = {
        "reviews": [],
        "title":   None,
        "rating":  None,
        "images":  [],
        "error":   None,
    }

    asin = _extract_asin(url)
    if not asin:
        result["error"] = "Could not extract ASIN from the Amazon URL."
        return result

    print(f"[amazon] ASIN: {asin}")

    driver = get_driver()
    try:
        all_reviews    = []
        seen_global    = set()
        consecutive_empty = 0
        hard_limit     = _DEFAULT_MAX_PAGES

        for page_num in range(1, _DEFAULT_MAX_PAGES + 1):
            page_url = _reviews_url(asin, page_num)
            print(f"[amazon] Page {page_num}/{hard_limit}")

            driver.get(page_url)
            time.sleep(2.5)   # Amazon needs a longer wait than Flipkart

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # ── Bot / CAPTCHA detection ────────────────────────────────────────
            page_text = soup.get_text(" ", strip=True).lower()
            if any(k in page_text[:800] for k in ["robot check", "captcha", "sorry, we"]):
                result["error"] = "Amazon bot/CAPTCHA wall detected. Try again later."
                break
            if "sign in" in page_text[:400] and not soup.select('div[data-hook="review"]'):
                result["error"] = "Amazon requires sign-in to view reviews."
                break

            # ── Page-1 metadata ───────────────────────────────────────────────
            if page_num == 1:
                result["title"]  = _extract_product_title(soup)
                result["rating"] = _extract_product_rating(soup)
                total = _detect_total(soup)
                if total:
                    import math
                    hard_limit = min(math.ceil(total / _REVIEWS_PER_PAGE),
                                     _DEFAULT_MAX_PAGES)
                    print(f"[amazon] {total} total reviews, "
                          f"scraping up to {hard_limit} pages")

            # ── Extract & dedup ───────────────────────────────────────────────
            page_reviews = _extract_reviews(soup)
            new = []
            for r in page_reviews:
                norm = re.sub(r"\s+", " ", r["text"]).strip()
                if norm not in seen_global:
                    seen_global.add(norm)
                    new.append(r)

            if not new:
                consecutive_empty += 1
                print(f"[amazon] Page {page_num} → 0 new "
                      f"({consecutive_empty}/2 empty in a row)")
                if consecutive_empty >= 2:
                    print("[amazon] Stopping — reviews exhausted")
                    break
            else:
                consecutive_empty = 0
                all_reviews.extend(new)
                print(f"[amazon] Page {page_num} → {len(new)} new "
                      f"(total: {len(all_reviews)})")

            if page_num >= hard_limit:
                print(f"[amazon] Reached page limit ({hard_limit}), stopping")
                break

        result["reviews"] = all_reviews
        print(f"[amazon] Total reviews collected: {len(all_reviews)}")

        if not all_reviews and not result["error"]:
            result["error"] = "No reviews found. Amazon may have changed its layout."

    except Exception as exc:
        result["error"] = f"Scraping error: {exc}"
        import traceback; traceback.print_exc()
    finally:
        driver.quit()

    return result
