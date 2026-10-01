from django import forms
from django.utils import timezone
from .models import PantryItem


class PantryForm(forms.ModelForm):
    class Meta:
        model = PantryItem
        fields = ["name", "category", "quantity", "unit", "location", "expires_on", "stored_on", "image_url", "barcode"]
        widgets = {key: forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d") for key in ("expires_on", "stored_on")}

    def clean_stored_on(self):
        value = self.cleaned_data["stored_on"]
        if value > timezone.localdate():
            raise forms.ValidationError("Tanggal masuk tidak boleh berada di masa depan.")
        return value
