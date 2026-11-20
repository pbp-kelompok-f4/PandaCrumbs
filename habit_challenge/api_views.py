from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import ChallengePlan, Completion
from .serializers import ChallengePlanSerializer, CompletionSerializer


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def plan_list_create(request):
    if request.method == "GET":
        plans = ChallengePlan.objects.filter(user=request.user)
        return Response(ChallengePlanSerializer(plans, many=True).data, status=status.HTTP_200_OK)

    serializer = ChallengePlanSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def plan_detail(request, pk):
    plan = get_object_or_404(ChallengePlan, pk=pk, user=request.user)

    if request.method == "GET":
        return Response(ChallengePlanSerializer(plan).data, status=status.HTTP_200_OK)

    if request.method in ("PUT", "PATCH"):
        serializer = ChallengePlanSerializer(
            plan, data=request.data, partial=(request.method == "PATCH")
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    plan.delete()
    return Response(
        {"message": "Rencana tantangan berhasil dihapus."},
        status=status.HTTP_204_NO_CONTENT,
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def completion_list_create(request):
    if request.method == "GET":
        completions = Completion.objects.filter(user=request.user)
        return Response(
            CompletionSerializer(completions, many=True).data,
            status=status.HTTP_200_OK,
        )

    serializer = CompletionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    plan = serializer.validated_data.get("plan")
    if plan and plan.user != request.user:
        return Response(
            {"detail": "Rencana tantangan tidak ditemukan."},
            status=status.HTTP_403_FORBIDDEN,
        )

    kind = serializer.validated_data["kind"]
    points = 15 if kind == Completion.Kind.SHARE else 10

    try:
        completion = serializer.save(user=request.user, points=points)
    except IntegrityError:
        return Response(
            {"detail": "Kamu sudah melakukan check-in untuk kategori ini hari ini."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response(CompletionSerializer(completion).data, status=status.HTTP_201_CREATED)