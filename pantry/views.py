from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import PantryForm
from .models import PantryItem


@login_required
def index(request):
    items = PantryItem.objects.filter(owner=request.user)
    query = request.GET.get("q", "").strip()[:120]
    status = request.GET.get("status", "")
    location = request.GET.get("location", "")
    category = request.GET.get("category", "")
    if query:
        items = items.filter(name__icontains=query)
    if location:
        items = items.filter(location=location)
    if category:
        items = items.filter(category=category)
    today = timezone.localdate()
    if status == "expired":
        items = items.filter(expires_on__lt=today)
    elif status == "soon":
        items = items.filter(expires_on__range=(today, today + timedelta(days=3)))
    elif status == "safe":
        items = items.filter(expires_on__gt=today + timedelta(days=3))
    context = dict(items=items, q=query, status=status, location=location, category=category,
                   locations=PantryItem.LOCATIONS, categories=PantryItem.CATEGORIES, active="pantry")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"html": render_to_string("pantry/cards.html", context, request=request)})
    return render(request, "pantry/index.html", context)


@login_required
def edit(request, pk=None):
    item = get_object_or_404(PantryItem, pk=pk, owner=request.user) if pk else None
    form = PantryForm(request.POST or None, instance=item)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.owner = request.user
        item.save()
        messages.success(request, "Bahan makanan berhasil disimpan.")
        return redirect("pantry:index")
    return render(request, "pantry/form.html", {"form": form, "item": item, "active": "pantry"})


@login_required
@require_POST
def consume(request, pk):
    with transaction.atomic():
        item = get_object_or_404(PantryItem.objects.select_for_update(), pk=pk, owner=request.user)
        changed = PantryItem.objects.filter(pk=item.pk, quantity__gt=1).update(quantity=F("quantity") - 1)
        if not changed:
            PantryItem.objects.filter(pk=item.pk, quantity=1).delete()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect("pantry:index")


@login_required
def delete(request, pk):
    item = get_object_or_404(PantryItem, pk=pk, owner=request.user)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Bahan makanan dihapus.")
        return redirect("pantry:index")
    return render(request, "confirm_delete.html", {"object": item, "cancel_url": "pantry:index", "active": "pantry"})
