from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import get_user_model
from Profile.models import Wallet
from Profile.models import RecentEarnings
from datetime import timedelta
from django.utils import timezone



User = get_user_model()

class SpinWheelView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        # Get the number of points earned from the spin wheel from the POST request data
        points = request.data.get('points')
        if not points:
            return Response({'message': 'Points parameter is missing'}, status=400)

        # Get the authenticated user from the request
        user = request.user

        user_recent_earning = RecentEarnings.objects.create(user=user, way_to_earn="Spin Wheel", point_earned=points)
        user_recent_earning.save()

        # Add the points to the user's account
        user_wallet = Wallet.objects.get(user=user)
        user_wallet.points += points
        user_wallet.save()

        return Response({'message': f'{points} points added to your account.'}, status=200)


class DailyCheckIn(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, args, **kwargs):

        # Get the authenticated user from the request
        user = request.user

        # Check if the user has already earned points for a daily check-in in the last 24 hours
        last_check_in = RecentEarnings.objects.filter(user=user, way_to_earn='Daily Check-In').order_by('-created_at').first()
        if last_check_in and timezone.now() - last_check_in.created_at < timedelta(days=1):
            return Response({'message': 'You have already earned points for a daily check-in in the last 24 hours.'}, status=400)

        # Add the points to the user's account
        user_wallet = Wallet.objects.get(user=user)
        user_wallet.points += 50
        user_wallet.save()

        RecentEarnings.objects.create(user=user, way_to_earn="Daily Check-In", point_earned=50)

        return Response({'message': f'{50} points added to your account.'}, status=200)
    

class WalletView(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request, *args, **kwargs):
        # Get the authenticated user from the request
        user = request.user

        # Get the user's wallet
        try:
            user_wallet = Wallet.objects.select_related('user').get(user=user)
        except Wallet.DoesNotExist:
            return Response({'message': 'Wallet does not exist'}, status=400)

        # Return the current points in the user's wallet
        return Response({'message': str(user_wallet.points)}, status=200)
