"""Responses shared by pages with progressively enhanced AJAX controls."""

from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string


def is_ajax(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def render_results(request, template, partial, context):
    if is_ajax(request):
        return JsonResponse(
            {"html": render_to_string(partial, context, request=request)}
        )
    return render(request, template, context)
