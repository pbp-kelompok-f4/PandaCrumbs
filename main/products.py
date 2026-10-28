"""Open Food Facts lookup, cache, and request throttling."""

import hashlib

import requests
from django.conf import settings
from django.core.cache import cache

SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
CACHE_SECONDS = 3600
SEARCH_INTERVAL_SECONDS = 7


class ProductSearchError(Exception):
    def __init__(self, message, status):
        super().__init__(message)
        self.status = status


def pantry_category_for(categories):
    value = categories.casefold()
    if any(term in value for term in ("yogurt", "yoghurt", "yaourt")):
        return "Yogurt"
    if any(term in value for term in ("fruit", "fruits", "buah")):
        return "Buah Segar"
    if any(term in value for term in ("vegetable", "vegetables", "sayur")):
        return "Sayuran"
    if any(
        term in value for term in ("dairy", "dairies", "milk", "cheese", "susu")
    ):
        return "Susu"
    if any(
        term in value
        for term in (
            "meat",
            "fish",
            "seafood",
            "poultry",
            "egg",
            "eggs",
            "protein",
            "tofu",
            "tempe",
        )
    ):
        return "Protein"
    if any(
        term in value
        for term in (
            "bread",
            "cereal",
            "grain",
            "rice",
            "pasta",
            "flour",
            "legume",
            "bean",
            "beans",
        )
    ):
        return "Bahan Pokok"
    return ""


def search_products(query, category=""):
    query = query.strip()[:80]
    category = category.strip()[:60]
    if len(query) < 2:
        raise ProductSearchError("Masukkan minimal dua karakter.", 400)

    key = "off:v2:" + hashlib.sha256((query + "|" + category).encode()).hexdigest()
    products = cache.get(key)
    if products is not None:
        return products
    if not cache.add("off-search-gate", True, SEARCH_INTERVAL_SECONDS):
        raise ProductSearchError(
            "Tunggu beberapa detik sebelum mencari produk lain.", 429
        )

    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 8,
        "fields": "code,product_name,categories,image_front_small_url",
    }
    if category:
        params.update(tagtype_0="categories", tag_contains_0="contains", tag_0=category)
    try:
        response = requests.get(
            SEARCH_URL,
            params=params,
            headers={"User-Agent": settings.OFF_USER_AGENT},
            timeout=(3, 8),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(
            payload.get("products"), list
        ):
            raise ValueError("Unexpected product payload")
        products = []
        for product in payload["products"]:
            if not isinstance(product, dict) or not product.get("product_name"):
                continue
            categories = str(product.get("categories", ""))[:160]
            products.append(
                {
                    "name": str(product.get("product_name", ""))[:120],
                    "barcode": str(product.get("code", ""))[:32],
                    "category": categories,
                    "pantry_category": pantry_category_for(categories),
                    "image": product.get("image_front_small_url", ""),
                }
            )
    except (requests.RequestException, ValueError, TypeError) as error:
        raise ProductSearchError(
            "Open Food Facts belum dapat dihubungi. Isi data secara manual atau coba lagi nanti.",
            503,
        ) from error
    cache.set(key, products, CACHE_SECONDS)
    return products
