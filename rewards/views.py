from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from Profile.models import Wallet

User = get_user_model()

class SpinWheelView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        # Get the number of points earned from the spin wheel from the POST request data
        points = request.data.get('points')
        if not points:
            return Response({'error': 'Points parameter is missing'}, status=400)

        # Get the authenticated user from the request
        user = request.user

        # Add the points to the user's account
        user_wallet = Wallet.objects.get(user=user)
        user_wallet.points += points
        user_wallet.save()

        return Response({'success': f'{points} points added to your account.'}, status=200)
