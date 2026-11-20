from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import FoodWasteLog
from .serializers import FoodWasteLogSerializer


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def waste_log_list_create(request):
    if request.method == "GET":
        queryset = FoodWasteLog.objects.filter(owner=request.user)
        reason = request.query_params.get("reason")
        if reason:
            queryset = queryset.filter(reason=reason)
        serializer = FoodWasteLogSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    serializer = FoodWasteLogSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def waste_log_detail(request, pk):
    log = get_object_or_404(FoodWasteLog, pk=pk, owner=request.user)

    if request.method == "GET":
        return Response(FoodWasteLogSerializer(log).data, status=status.HTTP_200_OK)

    if request.method in ("PUT", "PATCH"):
        serializer = FoodWasteLogSerializer(
            log, data=request.data, partial=(request.method == "PATCH")
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    log.delete()
    return Response(
        {"message": "Catatan food waste berhasil dihapus."},
        status=status.HTTP_204_NO_CONTENT,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def waste_summary(request):
    queryset = FoodWasteLog.objects.filter(owner=request.user)
    total_loss = queryset.aggregate(total=Sum("estimated_loss"))["total"] or 0
    return Response(
        {
            "total_logs": queryset.count(),
            "total_estimated_loss": total_loss,
        },
        status=status.HTTP_200_OK,
    )