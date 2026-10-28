from django import forms
from django.utils import timezone
from .models import FoodOffer, FoodClaim

class FoodOfferForm(forms.ModelForm):
    class Meta:
        model = FoodOffer
        fields = [
            "title",
            "category",
            "description",
            "portions",
            "pickup_location",
            "contact_info",
            "pickup_deadline",
            "latitude",
            "longitude",
            "image_url",
        ]

        widgets = {
            "pickup_deadline": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "class": "form-input",
                },
                format="%Y-%m-%dT%H:%M"
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Jelaskan kondisi makanan, takaran, atau instruksi penyimpanan...",
                }
            ),
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.pickup_deadline:
            self.initial["pickup_deadline"] = self.instance.pickup_deadline.strftime("%Y-%m-%dT%H:%M")

    def clean_portions(self):
            portions = self.cleaned_data.get("portions")
            if portions is None or portions < 1:
                raise forms.ValidationError("Jumlah porsi minimal adalah 1 porsi.")
            return portions

    def clean_pickup_deadline(self):
        deadline = self.cleaned_data.get("pickup_deadline")
        if deadline and deadline <= timezone.now():
            raise forms.ValidationError("Batas waktu penjemputan harus berada di masa yang akan datang.")
        return deadline

class FoodClaimForm(forms.ModelForm):
    class Meta:
        model = FoodClaim
        fields = ["portions_claimed", "notes"]
        widgets = {
            "portions_claimed": forms.NumberInput(
                attrs= {
                    "min": 1,
                    "class": "form-input",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows":3,
                    "placeholder": "Contoh: Perkiraan tiba jam 16.00 dengan menggunakan motor...",
                }
            ),
        }

    def clean_portions_claimed(self):
        portions = self.cleaned_data.get("portions_claimed")
        if portions is None or portions < 1:
            raise forms.ValidationError("Porsi yang diklaim minimal berjumlah 1.")
        return portions