from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Min, Sum
from django.db.models.functions import Lower, Trim
from django.shortcuts import get_object_or_404, redirect, render
from main.http import render_results
from django.views.decorators.http import require_http_methods

from .forms import AuditFilterForm, FoodWasteLogForm
from .models import FoodWasteLog


@login_required
@require_http_methods(["GET"])
def index(request):
    filter_form = AuditFilterForm(request.GET)
    filters_valid = filter_form.is_valid()
    entries = FoodWasteLog.objects.filter(owner=request.user)
    if filters_valid:
        filters = filter_form.cleaned_data
        if filters["start_date"]:
            entries = entries.filter(wasted_on__gte=filters["start_date"])
        if filters["end_date"]:
            entries = entries.filter(wasted_on__lte=filters["end_date"])
        if filters["reason"]:
            entries = entries.filter(reason=filters["reason"])
    else:
        entries = entries.none()

    summary = entries.aggregate(
        total_entries=Count("pk"), valued_entries=Count("estimated_loss"), estimated_loss=Sum("estimated_loss"),
    )
    frequent_reason = entries.order_by().values("reason").annotate(count=Count("pk")).order_by("-count", "reason").first()
    summary["top_reason"] = dict(FoodWasteLog.REASONS)[frequent_reason["reason"]] if frequent_reason else None
    summary["top_reason_count"] = frequent_reason["count"] if frequent_reason else 0
    # Count occurrences, not quantities with incompatible units.
    grouped_foods = (
        entries.order_by().annotate(food_key=Lower(Trim("food_name")))
        .values("food_key").annotate(count=Count("pk"), display_name=Min("food_name"))
        .order_by("-count", "food_key")[:3]
    )
    top_foods = [{"food_name": item["display_name"], "count": item["count"]} for item in grouped_foods]
    context = {
        "entries": entries, "filter_form": filter_form, "filters_valid": filters_valid,
        "summary": summary, "top_foods": top_foods, "active": "waste_audit",
    }
    return render_results(request, "waste_audit/index.html", "waste_audit/results.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def edit(request, pk=None):
    entry = get_object_or_404(FoodWasteLog, pk=pk, owner=request.user) if pk is not None else None
    form = FoodWasteLogForm(request.POST if request.method == "POST" else None, instance=entry)
    if request.method == "POST" and form.is_valid():
        entry = form.save(commit=False)
        entry.owner = request.user
        entry.save()
        messages.success(request, "Catatan makanan terbuang berhasil disimpan.")
        return redirect("waste_audit:index")
    return render(request, "waste_audit/form.html", {
        "form": form, "entry": entry, "active": "waste_audit", "product_context": "audit",
    })


@login_required
@require_http_methods(["GET", "POST"])
def delete(request, pk):
    entry = get_object_or_404(FoodWasteLog, pk=pk, owner=request.user)
    if request.method == "POST":
        entry.delete()
        messages.success(request, "Catatan makanan terbuang dihapus.")
        return redirect("waste_audit:index")
    return render(request, "waste_audit/confirm_delete.html", {"entry": entry, "active": "waste_audit"})
