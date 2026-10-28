from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET
from .forms import RegistrationForm
from .products import ProductSearchError, search_products


def show_landing_page(request):
    return render(request, "landing.html")


def register(request):
    if request.user.is_authenticated:
        return redirect("pantry:index")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(
            request, "Akun berhasil dibuat. Mulai tambahkan bahan makananmu."
        )
        return redirect("pantry:index")
    return render(request, "registration/register.html", {"form": form})


@login_required
@require_GET
def product_search(request):
    try:
        products = search_products(
            request.GET.get("q", ""), request.GET.get("category", "")
        )
    except ProductSearchError as error:
        return JsonResponse({"error": str(error)}, status=error.status)
    return JsonResponse({"products": products})