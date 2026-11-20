import json
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def _parse_body(request):
    if request.content_type == "application/json":
        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return {}
    return request.POST


@csrf_exempt
def login_api(request):
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "Method tidak diizinkan."}, status=405)

    data = _parse_body(request)
    username = data.get("username", "").strip()
    password = data.get("password", "")

    user = authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            auth_login(request, user)
            return JsonResponse(
                {
                    "status": True,
                    "message": "Login berhasil!",
                    "username": user.username,
                },
                status=200,
            )
        return JsonResponse(
            {"status": False, "message": "Akun dinonaktifkan."},
            status=401,
        )

    return JsonResponse(
        {"status": False, "message": "Username atau password salah."},
        status=401,
    )


@csrf_exempt
def register_api(request):
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "Method tidak diizinkan."}, status=405)

    data = _parse_body(request)
    username = data.get("username", "").strip()
    password = data.get("password", "")
    password_confirm = data.get("password_confirm") or data.get("password2") or password

    if not username or not password:
        return JsonResponse(
            {"status": False, "message": "Username dan password wajib diisi."},
            status=400,
        )
    if password != password_confirm:
        return JsonResponse(
            {"status": False, "message": "Konfirmasi password tidak cocok."},
            status=400,
        )
    if User.objects.filter(username=username).exists():
        return JsonResponse(
            {"status": False, "message": "Username sudah digunakan."},
            status=400,
        )

    user = User.objects.create_user(username=username, password=password)
    return JsonResponse(
        {
            "status": True,
            "message": "Akun berhasil dibuat!",
            "username": user.username,
        },
        status=201,
    )


@csrf_exempt
def logout_api(request):
    username = request.user.username if request.user.is_authenticated else ""
    try:
        auth_logout(request)
        return JsonResponse(
            {
                "status": True,
                "message": "Logout berhasil!",
                "username": username,
            },
            status=200,
        )
    except Exception:
        return JsonResponse({"status": False, "message": "Logout gagal."}, status=401)