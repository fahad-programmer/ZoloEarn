from rest_framework.views import APIView, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import get_user_model
from Profile.models import Wallet
from Profile.models import RecentEarnings
from datetime import timedelta, timezone
from datetime import timedelta
from django.utils import timezone
from .models import SpinWheel, MonsterHunter, TickTacToe
from django.utils import timezone as django_timezone
from django.db.models import Sum
from .serializers import UserStatsSerializer
from rest_framework import generics


User = get_user_model()


class SpinWheelView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):

        # Getting the spinwheel object
        user_spin_object = SpinWheel.objects.get(user=request.user)

        # Continue with the normal flow if the user has spins available or has not played in the last 24 hours
        # Get the number of points earned from the spin wheel from the POST request data
        points = request.data.get('points')

        # Rest of the code to handle points earned goes here...

        # Adding Some Checks
        if points == 0:

            user_spin_object.spin_available -= 1
            user_spin_object.save()

            return Response({"message": "better luck next time"}, status=status.HTTP_200_OK)

        elif points == 11:
            return Response({"message": "free turn"}, status=status.HTTP_200_OK)

        elif points == 22:

            user_spin_object.spin_available -= 1
            user_spin_object.save()

            userMonsterHunt = MonsterHunter.objects.get(user=request.user)
            userMonsterHunt.turn_available += 1
            userMonsterHunt.save()
            return Response({"message": "free monster hunt turn"}, status=status.HTTP_200_OK)

        elif points == 33:

            user_spin_object.spin_available -= 1
            user_spin_object.save()

            userTickTacToe = TickTacToe.objects.get(user=request.user)
            userTickTacToe.turn_available += 1
            userTickTacToe.save()
            return Response({"message": "free monster hunt turn"}, status=status.HTTP_200_OK)

        else:
            # Get the authenticated user from the request
            user = request.user

            user_spin_object.spin_available -= 1
            user_spin_object.save()

            user_recent_earning = RecentEarnings.objects.create(
                user=user, way_to_earn="Spin Wheel", point_earned=points)
            user_recent_earning.save()

            # Add the points to the user's account
            user_wallet = Wallet.objects.get(user=user)
            user_wallet.points += points
            user_wallet.save()

            return Response({'message': f'{points} points added to your account.'}, status=status.HTTP_200_OK)


class DailyCheckIn(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request,  **kwargs):
        # Get the authenticated user from the request
        user = request.user

        # Check when the user last claimed the award
        last_claimed = RecentEarnings.objects.filter(
            user=user, way_to_earn='Daily Check-In').order_by('-created_at').first()

        if last_claimed and last_claimed.created_at > timezone.now() - timedelta(hours=24):
            # User has already claimed the award in the last 24 hours
            return Response({'message': 'You have already claimed the award in the last 24 hours.'}, status=400)

        # Add the points to the user's account
        user_wallet = Wallet.objects.get(user=user)
        user_wallet.points += 50
        user_wallet.save()

        RecentEarnings.objects.create(
            user=user, way_to_earn="Daily Check-In", point_earned=50)

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
            return Response({'message': 'Wallet does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        # Return the current points in the user's wallet
        return Response({'message': str(user_wallet.points)}, status=status.HTTP_200_OK)


class UserSpinTurn(APIView):

    authentication_classes = [TokenAuthentication]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Get the user's spin wheel object
        try:
            userWheelObject = SpinWheel.objects.get(user=user)
            last_spin_time = userWheelObject.last_played_at
            current_time = django_timezone.now()
            time_since_last_spin = current_time - last_spin_time
            if time_since_last_spin >= timedelta(hours=24):
                userWheelObject.spin_available = 1
                userWheelObject.save()
        except SpinWheel.DoesNotExist:
            return Response({'message': 'Spin Wheel Object Failed'}, status=status.HTTP_400_BAD_REQUEST)

        # Return the current spins available for the user
        return Response({'message': str(userWheelObject.spin_available)}, status=status.HTTP_200_OK)


class UserSpinFree(APIView):

    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        # Get the authenticated user from the request
        user = request.user

        # Get the user's wallet
        try:
            userWheelObject = SpinWheel.objects.get(user=user)
            userWheelObject.spin_available += 1
            userWheelObject.save()

        except Wallet.DoesNotExist:
            return Response({'message': 'Spin Wheel Object Failed'}, status=status.HTTP_400_BAD_REQUEST)

        # Return the current points in the user's wallet
        return Response({'message': str(userWheelObject.spin_available)}, status=status.HTTP_200_OK)


class userTTCAvailabeTurn(APIView):

    authentication_classes = [TokenAuthentication]

    def get(self, request, *args, **kwargs):
        user = request.user

        #Getting user turns
        try:
            userTTCObject = TickTacToe.objects.get(user=user)
            last_played_time = userTTCObject.last_played_at
            current_time = django_timezone.now()
            time_since_last_played = current_time - last_played_time
            if time_since_last_played >= timedelta(hours=24):
                userTTCObject.turn_available = 1
                userTTCObject.save()
            return Response({"message": str(userTTCObject.turn_available)}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "Some Error Occured"}, status=status.HTTP_400_BAD_REQUEST)


class addUserTTCTurn(APIView):

    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        user = request.user

        #Adding the user turns
        userTTCObject = TickTacToe.objects.get(user=user)
        userTTCObject.turn_available += 1
        userTTCObject.save()

        #Returning Response
        return Response({"message":"Free Turn Given"}, status=status.HTTP_200_OK)


class TTCApiView(APIView):

    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        user = request.user

        #TTC Object
        userTTCObject = TickTacToe.objects.get(user=user)
        userTTCObject.turn_available -= 1
        userTTCObject.save()

        #Adding entry to recent earnings
        user_recent_earning = RecentEarnings.objects.create(user=user, way_to_earn="Tic Tac Toe", point_earned=50)
        user_recent_earning.save()

        #Now adding points to the user wallet ()
        userWallet = Wallet.objects.get(user=user)
        userWallet.points += 50
        userWallet.save()

        return Response({"message" : "Points Added To The Wallet"}, status=status.HTTP_200_OK)


class TTCLoseApi(APIView):

    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        user = request.user

        #TTC Object
        userTTCObject = TickTacToe.objects.get(user=user)
        userTTCObject.turn_available -= 1
        userTTCObject.save()

        return Response({"message":"User Lost A Game"}, status=status.HTTP_400_BAD_REQUEST)


class AllUserStats(generics.ListAPIView):

    authentication_classes = [TokenAuthentication]
    serializer_class = UserStatsSerializer

    def get_queryset(self):
        return User.objects.annotate(points=Sum('wallet__points')).order_by('-points')[:50]

