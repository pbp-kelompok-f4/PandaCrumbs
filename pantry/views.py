from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from main.http import is_ajax, render_results

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
        items = items.filter(
            expires_on__range=(
                today,
                today + timedelta(days=PantryItem.EXPIRING_SOON_DAYS),
            )
        )
    elif status == "safe":
        items = items.filter(
            expires_on__gt=today + timedelta(days=PantryItem.EXPIRING_SOON_DAYS)
        )
    items = list(items)
    location_groups = []
    for location, _label in PantryItem.LOCATIONS:
        location_items = [item for item in items if item.location == location]
        if not location_items:
            continue
        status_groups = []
        for urgency in ("expired", "soon", "safe"):
            grouped_items = [item for item in location_items if item.status == urgency]
            if grouped_items:
                status_groups.append(
                    {
                        "status": urgency,
                        "label": grouped_items[0].status_label,
                        "items": grouped_items,
                    }
                )
        location_groups.append(
            {
                "location": location,
                "count": len(location_items),
                "status_groups": status_groups,
            }
        )
    context = dict(
        location_groups=location_groups,
        q=query,
        status=status,
        location=location,
        category=category,
        locations=PantryItem.LOCATIONS,
        categories=PantryItem.CATEGORIES,
        active="pantry",
    )
    return render_results(request, "pantry/index.html", "pantry/cards.html", context)


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
    return render(
        request, "pantry/form.html", {"form": form, "item": item, "active": "pantry"}
    )


@login_required
@require_POST
def consume(request, pk):
    with transaction.atomic():
        item = get_object_or_404(
            PantryItem.objects.select_for_update(), pk=pk, owner=request.user
        )
        if request.POST.get("consume_all") == "1":
            PantryItem.objects.filter(pk=item.pk).delete()
            deleted = True
        else:
            changed = PantryItem.objects.filter(pk=item.pk, quantity__gt=1).update(
                quantity=F("quantity") - 1
            )
            if not changed:
                PantryItem.objects.filter(pk=item.pk, quantity=1).delete()
                deleted = True
            else:
                deleted = False
    if is_ajax(request):
        return JsonResponse({"ok": True, "deleted": deleted})
    if request.POST.get("consume_all") == "1":
        messages.success(request, "Bahan ditandai habis dikonsumsi.")
    return redirect("pantry:index")


@login_required
def delete(request, pk):
    item = get_object_or_404(PantryItem, pk=pk, owner=request.user)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Bahan makanan dihapus.")
        return redirect("pantry:index")
    return render(
        request,
        "confirm_delete.html",
        {"object": item, "cancel_url": "pantry:index", "active": "pantry"},
    )
