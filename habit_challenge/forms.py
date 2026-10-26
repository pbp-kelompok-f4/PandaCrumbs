from django import forms
from django.utils import timezone
from .models import ChallengePlan


class CompletionForm(forms.Form):
    food = forms.CharField(
        label="Makanan atau bahan", max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Contoh: nasi sisa menjadi nasi goreng"}),
    )
    confirmed = forms.BooleanField(
        label="Saya sudah melakukan tantangan ini hari ini."
    )
    plan = forms.ModelChoiceField(
        label="Hitung untuk rencana", queryset=ChallengePlan.objects.none(),
        required=False, empty_label="Tanpa rencana pribadi",
    )

    def __init__(self, *args, user, kind, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        self.fields["plan"].queryset = ChallengePlan.objects.filter(
            user=user, kind=kind, starts_on__lte=today, ends_on__gte=today,
        )


class ChallengePlanForm(forms.ModelForm):
    class Meta:
        model = ChallengePlan
        fields = ["title", "kind", "target_days", "category", "food", "starts_on", "ends_on"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Contoh: habiskan stok sebelum belanja"}),
            "starts_on": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "ends_on": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def clean(self):
        data = super().clean()
        start, end, target = data.get("starts_on"), data.get("ends_on"), data.get("target_days")
        if start and end:
            if end < start:
                self.add_error("ends_on", "Tanggal selesai tidak boleh sebelum tanggal mulai.")
            elif target and target > (end - start).days + 1:
                self.add_error("target_days", "Target hari tidak boleh melebihi panjang periode.")
        if self.instance.pk and self.instance.completions.exists():
            if data.get("kind") != self.instance.kind:
                self.add_error("kind", "Jenis tantangan tidak dapat diubah setelah check-in pertama.")
            if start and end and self.instance.completions.exclude(completed_on__range=(start, end)).exists():
                self.add_error("ends_on", "Periode harus tetap mencakup semua check-in yang sudah tercatat.")
        return data
