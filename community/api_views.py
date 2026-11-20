from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import FoodOffer, FoodClaim
from .serializers import FoodOfferSerializer, FoodClaimSerializer


@api_view(["GET", "POST"])
def offer_list_create(request):
    if request.method == "GET":
        queryset = FoodOffer.objects.all()
        category = request.query_params.get("category")
        offer_status = request.query_params.get("status")
        if category:
            queryset = queryset.filter(category=category)
        if offer_status:
            queryset = queryset.filter(status=offer_status)
        serializer = FoodOfferSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    if not request.user.is_authenticated:
        return Response(
            {"detail": "Autentikasi diperlukan untuk membuat penawaran."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    serializer = FoodOfferSerializer(data=request.data)
    if serializer.is_valid():
        portions = serializer.validated_data.get("portions", 1)
        serializer.save(donor=request.user, remaining_portions=portions)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
def offer_detail(request, pk):
    offer = get_object_or_404(FoodOffer, pk=pk)

    if request.method == "GET":
        return Response(FoodOfferSerializer(offer).data, status=status.HTTP_200_OK)

    if not request.user.is_authenticated:
        return Response(
            {"detail": "Autentikasi diperlukan."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    if offer.donor != request.user:
        return Response(
            {"detail": "Kamu hanya bisa mengubah penawaran milik sendiri."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method in ("PUT", "PATCH"):
        serializer = FoodOfferSerializer(
            offer, data=request.data, partial=(request.method == "PATCH")
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    offer.delete()
    return Response(
        {"message": "Penawaran makanan berhasil dihapus."},
        status=status.HTTP_204_NO_CONTENT,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def claim_offer(request, pk):
    offer = get_object_or_404(FoodOffer, pk=pk)

    if offer.donor == request.user:
        return Response(
            {"detail": "Kamu tidak dapat mengklaim penawaran milik sendiri."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if offer.status != "AVAILABLE" or offer.is_expired or offer.remaining_portions <= 0:
        return Response(
            {"detail": "Penawaran makanan ini sudah tidak tersedia untuk diklaim."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = FoodClaimSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    portions_claimed = serializer.validated_data.get("portions_claimed", 1)
    if portions_claimed > offer.remaining_portions:
        return Response(
            {"detail": f"Sisa porsi hanya {offer.remaining_portions}."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        claim = serializer.save(offer=offer, claimer=request.user)
        offer.remaining_portions -= portions_claimed
        if offer.remaining_portions == 0:
            offer.status = "FULLY_CLAIMED"
        offer.save(update_fields=["remaining_portions", "status", "updated_at"])

    return Response(FoodClaimSerializer(claim).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([AllowAny])
def offer_claims_list(request, pk):
    offer = get_object_or_404(FoodOffer, pk=pk)
    claims = offer.claims.all()
    return Response(FoodClaimSerializer(claims, many=True).data, status=status.HTTP_200_OK)