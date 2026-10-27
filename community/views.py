from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F,Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import FoodClaimForm, FoodOfferForm
from .models import FoodClaim, FoodOffer

# Create your views here.
def index(request):
    tab = request.GET.get("tab", "all")
    query = request.GET.get("q", "").strip()[:100]
    category = request.GET.get("category", "").strip()

    offers = FoodOffer.objects.select_related("donor")

    now = timezone.now()
    counts = {
        "all": offers.count(),
        "available": offers.filter(status="AVAILABLE", pickup_deadline__gt=now).count(),
        "mine": offers.filter(donor=request.user).count() if request.user.is_authenticated else 0,
        "claimed": FoodClaim.objects.filter(claimer=request.user).values("offer").distinct().count() if request.user.is_authenticated else 0,
    }

    if tab == "available":
        offers = offers.filter(status="AVAILABLE", pickup_deadline__gt=now)
    elif tab == "mine":
        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}?tab={tab}")
        offers = offers.filter(donor=request.user)
    elif tab == "claimed":
        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}?tab={tab}")
        offers = offers.filter(claims__claimer=request.user).distinct()

    if query:
        offers = offers.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(pickup_location__icontains=query)
        )

    if category:
        offers = offers.filter(category=category)

    context = {
        "offers": offers,
        "counts": counts,
        "tab": tab,
        "q": query,
        "selected_category": category,
        "categories": [c[0] for c in FoodOffer.FOOD_CATEGORIES],
        "active": "community", 
    }

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string("community/cards.html", context, request=request)
        return JsonResponse({"html": html, "counts": counts})

    return render(request, "community/index.html", context)

def offer_detail(request, pk):
    offer = get_object_or_404(FoodOffer.objects.select_related("donor"), pk=pk)
    user_claims = offer.claims.filter(claimer=request.user) if request.user.is_authenticated else []
    claim_form = FoodClaimForm()

    can_view_contact = request.user.is_authenticated and (request.user == offer.donor or user_claims.exists())

    context = {
        "offer": offer,
        "user_claims": user_claims,
        "claim_form": claim_form,
        "can_view_contact": can_view_contact,
        "active": "community",
    }
    return render(request, "community/detail.html", context)

@login_required
def offer_create(request):
    form = FoodOfferForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        offer = form.save(commit=False)
        offer.donor = request.user
        offer.remaining_portions = offer.portions
        offer.save()
        messages.success(request, f"Penawaran makanan '{offer.title}' berhasil dibagikan ke komunitas.")
        return redirect("community:detail", pk=offer.pk)

    return render(request, "community/form.html", {"form": form, "active": "community"})

@login_required
def offer_edit(request, pk):
    offer = get_object_or_404(FoodOffer, pk=pk)
    if offer.donor != request.user:
        raise PermissionDenied("Anda tidak memiliki izin untuk mengedit penawaran ini.")

    form = FoodOfferForm(request.POST or None, instance=offer)
    if request.method == "POST" and form.is_valid():
        updated_offer = form.save(commit=False)
        diff = updated_offer.portions - offer.portions
        updated_offer.remaining.portions = max(0, offer.remaining_portions + diff)
        if updated_offer.remaining.portions > 0 and updated_offer.status == "FULLY_CLAIMED":
            updated_offer.status = "AVAILABLE"
        updated_offer.save()
        messages.success(request, "Perubahan penawaran berhasil disimpan.")
        return redirect("community:detail", pk=updated_offer.pk)

    return render(request, "community/form.html", {"form": form, "offer": offer, "active": "community"})

@login_required
def offer_delete(request, pk):
    offer = get_object_or_404(FoodOffer, pk=pk)
    if offer.donor != request.user:
        raise PermissionDenied("Anda tidak memiliki izin untuk menghapus penawaran ini.")

    if offer.claim.exists():
        messages.error(request, "Penawaran tidak dapat dihapus karena sudah memiliki klaim dari penerima.")
        return redirect("community:detail", pk=offer.pk)

    if request.method == "POST":
        offer.delete()
        messages.success(request, "Penawaran makanan berhasil dihapus.")
        return redirect("community:index")

    return render(request, "confirm_delete.html", {"object": offer, "cancel_url": "community:index", "active": "community"})

@login_required
@require_POST
def claim_food(request, pk):
    with transaction.atomic():
        offer = get_object_or_404(FoodOffer.objects.select_for_update(), pk=pk)

        if offer.donor == request.user:
            return JsonResponse({"error": "Anda tidak dapat mengklaim makanan yang Anda tawarkan sendiri."}, status=400)

        if offer.is_expired:
            return JsonResponse({"error": "Batas waktu penjemputan makanan ini sudah berakhir."}, status=400)

        if offer.status != "AVAILABLE" or offer.remaining_portions <= 0:
            return JsonResponse({"error": "Maaf, seluruh porsi makanan ini sudah habis diklaim."}, status=400)

        form = FoodClaimForm(request.POST)
        if not form.is_valid():
            error_message = next(iter(form.errors.value()))[0]
            return JsonResponse({"error": error_message}, status=400)

        portions = form.cleaned_data["portions_claimed"]
        if portions > offer.remaining_portions:
            return JsonResponse({"error": f"porsi yang diminta melebihi sisa tersedia ({offer.remaining_portions} porsi)."}, status=400)

        claim = form.save(commit=False)
        claim.offer = offer
        claim.claimer = request.user
        claim.save()

        offer.remaining_portions = F("remaining_portions") - portions
        offer.save(update_field=["remaining_portions", "updated_at"])
        offer.refresh_from_db()

        if offer.remaining_portions == 0:
            offer.status = "FULLY CLAIMED"
            offer.save(update_fields=["status"])

    return JsonResponse({"success":True, "message": f"Klaim {portions} porsi berhasil diajukan!", "remaining_portions": offer.remaining_portions, "status": offer.get_status_display(), "contact_info": offer.contact_info})