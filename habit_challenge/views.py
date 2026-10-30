from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.db.models import Count
from django.db import transaction
from django.db.models import F
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from urllib.parse import urlencode

from pantry.models import PantryItem
from community.models import FoodOffer
from main.http import is_ajax
from .forms import ChallengePlanForm, CompletionForm
from .models import ChallengePlan, Completion
from .services import progress_for


CHALLENGES = (
    {"kind": "pantry", "title": "Pakai stok tersisa", "subtitle": "Temukan menu dari pantry",
     "points": 10, "reward": "setelah memasak", "action": "Lihat bahan & resep"},
    {"kind": "leftovers", "title": "Olah makanan sisa", "subtitle": "Beri makanan sisa ide baru",
     "points": 10, "reward": "setelah memasak", "action": "Lihat resep olahan yang cocok"},
    {"kind": "share", "title": "Berbagi makanan", "subtitle": "Bagi makanan berlebih",
     "points": 15, "reward": "setelah berbagi", "action": "Catat makanan yang dibagikan"},
)


def dashboard_context(user, *, invalid_kind=None, invalid_form=None):
    today = timezone.localdate()
    from .services import award_community_post
    for offer in FoodOffer.objects.filter(donor=user, created_at__date=today):
        award_community_post(offer)
    completions = Completion.objects.filter(user=user)
    done = {entry.kind: entry for entry in completions.filter(completed_on=today)}
    pantry_names = list(PantryItem.objects.filter(
        owner=user, expires_on__gte=today,
    ).values_list("name", flat=True).distinct())
    ingredients = pantry_names[:4]
    cards = []
    for definition in CHALLENGES:
        card = dict(definition)
        kind = card["kind"]
        card["completion"] = done.get(kind)
        card["form"] = (invalid_form if kind == invalid_kind else
                        CompletionForm(user=user, kind=kind, auto_id=f"{kind}_%s"))
        card["open"] = kind == invalid_kind
        if kind == "pantry":
            card["tags"] = ingredients
            card["hint"] = "Dari pantry kamu" if ingredients else "Tambahkan bahan ke pantry untuk mulai."
            card["url"] = (reverse("recipes:index") + "?from_pantry=1"
                           if ingredients else reverse("pantry:add"))
            if not ingredients:
                card["action"] = "Tambah bahan ke pantry"
        elif kind == "leftovers":
            card["tags"] = ingredients
            card["hint"] = "Resep berdasarkan bahan pantry kamu" if ingredients else "Isi pantry untuk mencari resep."
            card["url"] = reverse("recipes:index") + "?from_pantry=1" if ingredients else reverse("pantry:add")
        else:
            card["tags"] = ["Untuk teman", "Untuk tetangga"]
            card["hint"] = "Posting penawaran makanan di Community untuk mendapat poin otomatis."
            card["url"] = reverse("community:add")
        cards.append(card)
    plans = list(ChallengePlan.objects.filter(user=user).annotate(checkin_count=Count("completions")))
    for plan in plans:
        plan.percent = min(100, plan.checkin_count * 100 // plan.target_days)
        plan.status = ("Tercapai" if plan.checkin_count >= plan.target_days else
                       "Selesai" if plan.ends_on < today else
                       "Akan datang" if plan.starts_on > today else "Aktif")
    return {
        "active": "habit_challenge", "progress": progress_for(completions, today),
        "cards": cards, "completed_count": len(done), "history": completions[:6],
        "plans": plans,
    }


@login_required
def index(request):
    return render(request, "habit_challenge/index.html", dashboard_context(request.user))


@login_required
@require_POST
def complete(request, kind):
    if kind in ("pantry", "leftovers"):
        return redirect("habit_challenge:cook_form", kind=kind)
    if kind == "share":
        return redirect("community:add")
    raise Http404("Tantangan tidak ditemukan.")


@login_required
def plan_edit(request, pk=None):
    plan = get_object_or_404(ChallengePlan, pk=pk, user=request.user) if pk else None
    form = ChallengePlanForm(request.POST if request.method == "POST" else None, instance=plan)
    if request.method == "POST" and form.is_valid():
        plan = form.save(commit=False)
        plan.user = request.user
        plan.save()
        messages.success(request, "Rencana tantangan berhasil disimpan.")
        return redirect("habit_challenge:index")
    return render(request, "habit_challenge/plan_form.html", {
        "form": form, "plan": plan, "active": "habit_challenge",
    })


@login_required
def plan_delete(request, pk):
    plan = get_object_or_404(ChallengePlan, pk=pk, user=request.user)
    if request.method == "POST":
        plan.delete()
        messages.success(request, "Rencana dihapus. Poin dan riwayat check-in kamu tetap tersimpan.")
        return redirect("habit_challenge:index")
    return render(request, "habit_challenge/plan_delete.html", {
        "plan": plan, "active": "habit_challenge",
    })


@login_required
@require_POST
def cook(request, kind):
    if kind not in ("pantry", "leftovers"):
        raise Http404("Jenis tantangan tidak dikenal")
    today = timezone.localdate()
    name = request.POST.get("food", "").strip()[:120]
    if not name:
        messages.error(request, "Isi nama masakan dahulu.")
        return redirect("habit_challenge:cook_form", kind=kind)
    try:
        with transaction.atomic():
            existing = Completion.objects.filter(user=request.user, kind=kind, completed_on=today).first()
            if existing:
                messages.info(request, "Poin memasak sudah dicatat hari ini; stok tidak dikurangi lagi.")
                return redirect("habit_challenge:index")
            items = list(PantryItem.objects.select_for_update().filter(
                owner=request.user, expires_on__gte=today).order_by("pk"))
            consumed = []
            for item in items:
                raw = request.POST.get(f"qty_{item.pk}", "0").strip()
                if not raw.isdecimal():
                    raise ValidationError(f"Jumlah {item.name} harus berupa bilangan bulat.")
                qty = int(raw)
                if qty > item.quantity:
                    raise ValidationError(f"Stok {item.name} hanya {item.quantity} {item.unit}.")
                if qty:
                    consumed.append((item, qty))
            if not consumed:
                raise ValidationError("Pilih setidaknya satu bahan yang dipakai.")
            for item, qty in consumed:
                if qty == item.quantity:
                    item.delete()
                else:
                    PantryItem.objects.filter(pk=item.pk).update(quantity=F("quantity") - qty)
            Completion.objects.create(user=request.user, kind=kind, completed_on=today,
                food=name, points=10)
        messages.success(request, "Masakan tercatat, stok pantry berkurang, dan +10 poin diterima!")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
        return redirect("habit_challenge:cook_form", kind=kind)
    return redirect("habit_challenge:index")


@login_required
def cook_form(request, kind):
    if kind not in ("pantry", "leftovers"):
        raise Http404("Jenis tantangan tidak dikenal")
    items = PantryItem.objects.filter(owner=request.user, expires_on__gte=timezone.localdate())
    return render(request, "habit_challenge/cook.html", {
        "items": items, "kind": kind, "active": "habit_challenge",
        "challenge_title": "Pakai stok tersisa" if kind == "pantry" else "Olah makanan sisa",
    })
