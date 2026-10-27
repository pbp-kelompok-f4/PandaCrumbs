from django import forms
from django.utils import timezone

from .models import FoodWasteLog


class FoodWasteLogForm(forms.ModelForm):
    class Meta:
        model = FoodWasteLog
        fields = ["food_name", "quantity", "unit", "wasted_on", "reason", "estimated_loss"]
        widgets = {
            "food_name": forms.TextInput(attrs={"placeholder": "Contoh: nasi putih"}),
            "quantity": forms.NumberInput(attrs={"min": "0.01", "step": "0.01", "inputmode": "decimal"}),
            "wasted_on": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "estimated_loss": forms.NumberInput(attrs={"min": "0", "step": "0.01", "inputmode": "decimal", "placeholder": "Contoh: 5000"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A dialog and the history filter can both contain an "Alasan" field.
        for name, field in self.fields.items():
            field.widget.attrs["id"] = f"audit-{name}"
        self.fields["wasted_on"].widget.attrs["max"] = timezone.localdate().isoformat()

    def clean_food_name(self):
        return " ".join(self.cleaned_data["food_name"].split())


class AuditFilterForm(forms.Form):
    start_date = forms.DateField(
        label="Dari tanggal", required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    end_date = forms.DateField(
        label="Sampai tanggal", required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    reason = forms.ChoiceField(label="Alasan", required=False, choices=[("", "Semua alasan")] + FoodWasteLog.REASONS)

    def clean(self):
        data = super().clean()
        start = data.get("start_date")
        end = data.get("end_date")
        if start and end and start > end:
            self.add_error("end_date", "Tanggal akhir harus sama dengan atau setelah tanggal mulai.")
        return data
