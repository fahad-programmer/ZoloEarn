import json
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import get_user_model
from Profile.models import Wallet, RecentEarnings, Profile
from datetime import timedelta, timezone
from datetime import timedelta
from rest_framework import viewsets
from django.utils import timezone
from .models import SpinWheel, MonsterHunter, TickTacToe, ZoloVideos, ZoloArticles
from django.utils import timezone as django_timezone
from .serializers import QuestionSerializer, QuizApiSerializer, QuizSerializer, MonsterHunterSerializer
from .models import Subject, Quiz, Questions

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

    def post(self, request, **kwargs):
        # Get the authenticated user from the request
        user = request.user

        # Check when the user last claimed the award
        last_claimed = RecentEarnings.objects.filter(
            user=user, way_to_earn='Daily Check-In').order_by('-created_at').first()

        if last_claimed and last_claimed.created_at == timezone.now().date():
            # User has already claimed the award today
            return Response({'message': 'You have already claimed the award today.'}, status=400)

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

        # Getting user turns
        try:
            userTTCObject = TickTacToe.objects.get(user=user)
            last_played_time = userTTCObject.last_played_at
            current_time = django_timezone.now()
            time_since_last_played = current_time - last_played_time
            if time_since_last_played >= timedelta(hours=6):
                userTTCObject.turn_available = 10
                userTTCObject.save()
            return Response({"message": str(userTTCObject.turn_available)}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "Some Error Occured"}, status=status.HTTP_400_BAD_REQUEST)


class addUserTTCTurn(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        user = request.user

        # Adding the user turns
        userTTCObject = TickTacToe.objects.get(user=user)
        userTTCObject.turn_available += 1
        userTTCObject.save()

        # Returning Response
        return Response({"message": "Free Turn Given"}, status=status.HTTP_200_OK)


class TTCApiView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        user = request.user

        # TTC Object
        userTTCObject = TickTacToe.objects.get(user=user)
        userTTCObject.turn_available -= 1
        userTTCObject.save()

        # Adding entry to recent earnings
        user_recent_earning = RecentEarnings.objects.create(user=user, way_to_earn="Tic Tac Toe", point_earned=5)
        user_recent_earning.save()

        # Now adding points to the user wallet ()
        userWallet = Wallet.objects.get(user=user)
        userWallet.points += 5
        userWallet.save()

        return Response({"message": "Points Added To The Wallet"}, status=status.HTTP_200_OK)


class TTCLoseApi(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        user = request.user

        # TTC Object
        userTTCObject = TickTacToe.objects.get(user=user)

        if userTTCObject.turn_available == 0:
            return Response({"message": "User Lost A Game"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            userTTCObject.turn_available -= 1
            userTTCObject.save()
            return Response({"message": "User Lost A Game"}, status=status.HTTP_400_BAD_REQUEST)


class MonsterHunterTurn(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request, *args, **kwargs):

        user = request.user

        # Getting user turns
        try:
            userMonsterHunterObject = MonsterHunter.objects.get(user=user)
            last_played_time = userMonsterHunterObject.last_played_at
            current_time = django_timezone.now()
            time_since_last_played = current_time - last_played_time
            if time_since_last_played >= timedelta(hours=12):
                userMonsterHunterObject.turn_available = 2
                userMonsterHunterObject.save()
            return Response({"message": str(userMonsterHunterObject.turn_available)}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "Some Error Occured"}, status=status.HTTP_400_BAD_REQUEST)


class MonsterHunterApi(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    serializer_class = MonsterHunterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            points = serializer.validated_data['points']

            # Add these points to wallet and deduct a turn
            userWallet = Wallet.objects.get(user=request.user)
            userWallet.points += int(points)
            userWallet.save()

            # Adding entry to recent earnings
            user_recent_earning = RecentEarnings.objects.create(user=request.user, way_to_earn="Monster Hunter",
                                                                point_earned=points)
            user_recent_earning.save()

            userMonsterHunterObj = MonsterHunter.objects.get(user=request.user)
            userMonsterHunterObj.turn_available = 0
            userMonsterHunterObj.save()

            return Response({"message": "Done"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "something happend"}, status=status.HTTP_400_BAD_REQUEST)


class QuizInQuestions(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    serializer_class = QuizSerializer

    def post(self, request, *args, **kwargs):

        # Deducting
        # Get the Quiz object for the authenticated user (modify the filter criteria as needed)
        userQuizInObj = Quiz.objects.get(user=request.user)

        # Deduct a turn for the user

        if userQuizInObj.turn_available == 0:
            return JsonResponse({"message": "You Have 0 Turns Available"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            userQuizInObj.turn_available -= 1
            userQuizInObj.save()

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            subject = serializer.validated_data['subject']

            # Getting the Subject object
            subject_obj = Subject.objects.get(subject=subject)

            # Getting the Questions
            questions = Questions.objects.filter(subject=subject_obj).order_by('?')[:10]

            # Serialize the questions
            serializer = QuestionSerializer(questions, many=True)
            serialized_questions = serializer.data

            # Return the serialized questions as a JSON response

            return JsonResponse(serialized_questions, safe=False)

        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuizApi(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    serializer_class = QuizApiSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            points = serializer.validated_data['points']

            # Add those points to the wallet and deduct a turn
            userWallet = Wallet.objects.get(user=request.user)
            userWallet.points += int(points)
            userWallet.save()

            # Adding entry to recent earnings
            user_recent_earning = RecentEarnings.objects.create(user=request.user, way_to_earn="Quiz In",
                                                                point_earned=points)
            user_recent_earning.save()

            return Response({"message": "Done"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Something happened"}, status=status.HTTP_400_BAD_REQUEST)


class AddQuizInApi(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args):
        # Get the Quiz object for the authenticated user (modify the filter criteria as needed)
        userQuizInObj = Quiz.objects.get(user=request.user)

        # Deduct a turn for the user
        userQuizInObj.turn_available += 1
        userQuizInObj.save()

        return Response({"message": "Done"}, status=status.HTTP_200_OK)


class AddMonsterHunterApi(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args):
        # getting the user object of monster hunter
        userMonsterHunterObj = MonsterHunter.objects.get(user=request.user)
        userMonsterHunterObj.turn_available += 1
        userMonsterHunterObj.save()

        return Response({"message": "Done"}, status=status.HTTP_200_OK)


class QuizInTurns(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Getting user turns
        try:
            userQuizInObj = Quiz.objects.get(user=user)
            last_played_time = userQuizInObj.last_played_at
            current_time = django_timezone.now()
            time_since_last_played = current_time - last_played_time
            if time_since_last_played >= timedelta(hours=6):
                userQuizInObj.turn_available = 1
                userQuizInObj.save()
            return Response({"message": str(userQuizInObj.turn_available)}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": "Some Error Occurred"}, status=status.HTTP_400_BAD_REQUEST)


# Function related to automating the quiz section
def load_questions_from_json_view(request):
    json_file = 'questions.json'  # Specify the path to your JSON file

    with open(json_file, 'r') as file:
        data = json.load(file)

    for item in data:
        subject_name = item['subject']
        subject, _ = Subject.objects.get_or_create(subject=subject_name)

        question = Questions.objects.create(
            subject=subject,
            question=item['question'],
            choice1=item['choices'][0],
            choice2=item['choices'][1],
            choice3=item['choices'][2],
            choice4=item['choices'][3],
            answer=item['correct_answer']
        )
        print("Done")

    return HttpResponse("All Questions Added")


class GetZoloVideos(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        # Retrieve ZoloVideos instance for the current user
        zolo_videos = ZoloVideos.objects.get(user=request.user)

        # Check if the user has 0 watched videos and return the message with remaining time
        if zolo_videos.videos_watched == 0 and zolo_videos.get_remaining_reset_time() > timezone.timedelta():
            remaining_reset_time = zolo_videos.get_remaining_reset_time()
            remaining_time_hours = remaining_reset_time.total_seconds() // 3600
            remaining_time_minutes = (remaining_reset_time.total_seconds() % 3600) // 60

            message = f"Please wait for {int(remaining_time_hours)} hours and {int(remaining_time_minutes)} minutes To Watch Again"
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

        # Get the unwatched video URLs based on the user's country
        unwatched_urls = zolo_videos.get_videos_by_country()

        return Response({"urls": unwatched_urls}, status=status.HTTP_200_OK)


class ZoloVideoApi(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        userZoloVideoObj = ZoloVideos.objects.get(user=request.user)

        userZoloVideoObj.videos_watched -= 1
        userZoloVideoObj.save()

        # Adding points to wallet
        userWallet = Wallet.objects.get(user=request.user)

        userWallet.points += 2
        userWallet.save()

        # Adding entry to recent earnings
        user_recent_earning = RecentEarnings.objects.create(user=request.user, way_to_earn="Zolo Videos",
                                                            point_earned=2)
        user_recent_earning.save()

        return Response({"message": "Completed the api transaction"})


class getZoloArticles(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        # Retrieve ZoloVideos instance for the current user
        zolo_articles = ZoloArticles.objects.get(user=request.user)

        # Check if the user has 0 watched videos and return the message with remaining time
        if zolo_articles.articles_read == 0 and zolo_articles.get_remaining_reset_time() > timezone.timedelta():
            remaining_reset_time = zolo_articles.get_remaining_reset_time()
            remaining_time_hours = remaining_reset_time.total_seconds() // 3600
            remaining_time_minutes = (remaining_reset_time.total_seconds() % 3600) // 60

            message = f"Please wait for {int(remaining_time_hours)} hours and {int(remaining_time_minutes)} minutes To Read Again"
            return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)

        # Get the unwatched articles URLs based on the user's country
        unread_articles = zolo_articles.get_user_articles()

        return Response({"urls": unread_articles}, status=status.HTTP_200_OK)


class ZoloArticlesApi(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        userZoloArticlesObj = ZoloArticles.objects.get(user=request.user)

        userZoloArticlesObj.articles_read -= 1
        userZoloArticlesObj.save()

        # Adding points to wallet
        userWallet = Wallet.objects.get(user=request.user)

        userWallet.points += 2
        userWallet.save()

        # Adding entry to recent earnings
        user_recent_earning = RecentEarnings.objects.create(user=request.user, way_to_earn="Zolo Articles",
                                                            point_earned=2)
        user_recent_earning.save()

        return Response({"message": "Completed the api transaction"})
