from django import forms
from .models import Recipe


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ["title", "ingredients", "steps", "portions", "minutes", "image_url"]
        widgets = {"ingredients": forms.Textarea(attrs={"rows": 5}), "steps": forms.Textarea(attrs={"rows": 7})}
