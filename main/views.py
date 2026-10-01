import hashlib
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET
from .forms import RegistrationForm


def show_landing_page(request):
    return render(request, "landing.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("pantry:index")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Akun berhasil dibuat. Mulai tambahkan bahan makananmu.")
        return redirect("pantry:index")
    return render(request, "registration/register.html", {"form": form})


@login_required
@require_GET
def product_search(request):
    query = request.GET.get("q", "").strip()[:80]
    category = request.GET.get("category", "").strip()[:60]
    if len(query) < 2:
        return JsonResponse({"error": "Masukkan minimal dua karakter."}, status=400)
    key = "off:" + hashlib.sha256((query + "|" + category).encode()).hexdigest()
    result = cache.get(key)
    if result is not None:
        return JsonResponse({"products": result})
    if not cache.add("off-search-gate", True, 7):
        return JsonResponse({"error": "Tunggu beberapa detik sebelum mencari produk lain."}, status=429)
    params = {"search_terms": query, "search_simple": 1, "action": "process", "json": 1, "page_size": 8,
              "fields": "code,product_name,categories,image_front_small_url"}
    if category:
        params.update(tagtype_0="categories", tag_contains_0="contains", tag_0=category)
    try:
        response = requests.get("https://world.openfoodfacts.org/cgi/search.pl", params=params,
            headers={"User-Agent": settings.OFF_USER_AGENT}, timeout=(3, 8))
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("products"), list):
            raise ValueError("Unexpected product payload")
        result = [{"name": str(p.get("product_name", ""))[:120], "barcode": str(p.get("code", ""))[:32],
                   "category": str(p.get("categories", ""))[:160],
                   "image": p.get("image_front_small_url", "")}
                  for p in payload["products"] if isinstance(p, dict) and p.get("product_name")]
    except (requests.RequestException, ValueError, TypeError):
        return JsonResponse({"error": "Open Food Facts belum dapat dihubungi. Isi data secara manual atau coba lagi nanti."}, status=503)
    cache.set(key, result, 3600)
    return JsonResponse({"products": result})
