from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from urllib.parse import urlencode

from pantry.models import PantryItem
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
    completions = Completion.objects.filter(user=user)
    done = {entry.kind: entry for entry in completions.filter(completed_on=today)}
    ingredients = list(PantryItem.objects.filter(
        owner=user, expires_on__gte=today,
    ).values_list("name", flat=True)[:4])
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
            card["url"] = (reverse("recipes:index") + "?" + urlencode({"ingredient": ingredients[0]})
                           if ingredients else reverse("pantry:add"))
            if not ingredients:
                card["action"] = "Tambah bahan ke pantry"
        elif kind == "leftovers":
            card["tags"] = ["Nasi matang", "Sayur matang"]
            card["hint"] = "Ide bahan yang bisa kamu olah"
            card["url"] = reverse("recipes:index") + "?" + urlencode({"q": "sisa"})
        else:
            card["tags"] = ["Untuk teman", "Untuk tetangga"]
            card["hint"] = "Community segera hadir. Catat berbagi langsung di sini."
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
    challenge = next((item for item in CHALLENGES if item["kind"] == kind), None)
    if challenge is None:
        raise Http404("Tantangan tidak ditemukan.")
    form = CompletionForm(request.POST, user=request.user, kind=kind, auto_id=f"{kind}_%s")
    if not form.is_valid():
        if is_ajax(request):
            return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
        return render(request, "habit_challenge/index.html", dashboard_context(
            request.user, invalid_kind=kind, invalid_form=form,
        ), status=400)
    # A database unique constraint also prevents rewards from parallel requests.
    _, created = Completion.objects.get_or_create(
        user=request.user, kind=kind, completed_on=timezone.localdate(),
        defaults={"food": form.cleaned_data["food"], "points": challenge["points"], "plan": form.cleaned_data["plan"]},
    )
    if created:
        message = f"Hebat! {challenge['title']} selesai. +{challenge['points']} poin untuk Pao."
    else:
        message = "Tantangan ini sudah kamu selesaikan hari ini. Kembali lagi besok, ya!"
    if is_ajax(request):
        return JsonResponse({"message": message, "html": render_to_string(
            "habit_challenge/dashboard.html", dashboard_context(request.user), request=request,
        )})
    messages.success(request, message)
    return redirect("habit_challenge:index")


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
