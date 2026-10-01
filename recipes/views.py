from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from .forms import RecipeForm
from .models import Bookmark, Recipe


def index(request):
    tab = request.GET.get("tab", "all")
    if tab in ("saved", "mine") and not request.user.is_authenticated:
        return redirect("/accounts/login/?next=" + request.path + "?tab=" + tab)
    recipes = Recipe.objects.select_related("author")
    saved = Bookmark.objects.filter(user=request.user) if request.user.is_authenticated else Bookmark.objects.none()
    counts = {"all": recipes.count(), "saved": saved.count(),
              "mine": recipes.filter(author=request.user).count() if request.user.is_authenticated else 0}
    if tab == "saved":
        recipes = recipes.filter(bookmark__user=request.user)
    elif tab == "mine":
        recipes = recipes.filter(author=request.user)
    query = request.GET.get("q", "").strip()[:120]
    ingredients = list(dict.fromkeys(x.strip()[:40] for x in request.GET.getlist("ingredient") if x.strip()))[:12]
    if query:
        recipes = recipes.filter(Q(title__icontains=query) | Q(ingredients__icontains=query))
    for ingredient in ingredients:
        recipes = recipes.filter(ingredients__icontains=ingredient)
    recipes = recipes.annotate(is_saved=Exists(saved.filter(recipe_id=OuterRef("pk"))))
    context = dict(recipes=recipes, counts=counts, q=query, ingredients=ingredients,
                   suggestions=["Bawang Merah", "Kecap Manis", "Tempe", "Mie Instan"],
                   tab=tab, active="recipes")
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"html": render_to_string("recipes/results.html", context, request=request)})
    return render(request, "recipes/index.html", context)


def detail(request, pk):
    recipe = get_object_or_404(Recipe.objects.select_related("author"), pk=pk)
    saved = request.user.is_authenticated and Bookmark.objects.filter(user=request.user, recipe=recipe).exists()
    return render(request, "recipes/detail.html", {"recipe": recipe, "saved": saved, "active": "recipes",
                  "ingredients": recipe.ingredients.splitlines(), "steps": recipe.steps.splitlines()})


@login_required
def edit(request, pk=None):
    recipe = get_object_or_404(Recipe, pk=pk, author=request.user) if pk else None
    form = RecipeForm(request.POST or None, instance=recipe)
    if request.method == "POST" and form.is_valid():
        recipe = form.save(commit=False)
        recipe.author = request.user
        recipe.save()
        messages.success(request, "Resep berhasil disimpan.")
        return redirect("recipes:detail", pk=recipe.pk)
    return render(request, "recipes/form.html", {"form": form, "recipe": recipe, "active": "recipes"})


@login_required
def delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, author=request.user)
    if request.method == "POST":
        recipe.delete()
        messages.success(request, "Resep dihapus.")
        return redirect("recipes:index")
    return render(request, "confirm_delete.html", {"object": recipe, "cancel_url": "recipes:index", "active": "recipes"})


@login_required
@require_POST
def bookmark(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    saved = request.POST.get("saved") == "1"
    if saved:
        Bookmark.objects.get_or_create(user=request.user, recipe=recipe)
    else:
        Bookmark.objects.filter(user=request.user, recipe=recipe).delete()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"saved": saved})
    return redirect("recipes:detail", pk=pk)
