import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView, status
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import get_user_model
from Profile.models import Wallet, RecentEarnings
from datetime import timedelta, timezone
from datetime import timedelta
from rest_framework import viewsets
from django.utils import timezone
from .models import SpinWheel, MonsterHunter, TickTacToe
from django.utils import timezone as django_timezone
from .serializers import QuestionSerializer, QuizApiSerializer, QuizSerializer, MonsterHunterSerializer
from .models import Subject, Quiz, Questions

User = get_user_model()


# noinspection PyMethodMayBeStatic
class SpinWheelView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        user_spin_object = get_object_or_404(SpinWheel, user=request.user)
        points = request.data.get('points')

        if self._is_zero_points(points):
            return self._handle_zero_points(user_spin_object)
        elif self._is_special_turn(points):
            return self._handle_special_turn(points, request)
        else:
            return self._handle_regular_points(user_spin_object, points, request)

    def _is_zero_points(self, points):
        return int(points) == 0

    def _handle_zero_points(self, user_spin_object):
        user_spin_object.spin_available -= 1
        user_spin_object.save()
        return Response({"message": "better luck next time"}, status=status.HTTP_200_OK)

    def _is_special_turn(self, points):
        return int(points) in (11, 22, 33)

    def _handle_special_turn(self, points, request):

        # Converting to the int datatype
        points = int(points)

        if points == 11:
            return Response({"message": "free turn"}, status=status.HTTP_200_OK)
        elif points == 22:
            self._handle_free_turn(user=request.user, game_model=MonsterHunter, message="free monster hunt turn")
        elif points == 33:
            self._handle_free_turn(user=request.user, game_model=TickTacToe, message="free tick-tac-toe turn")

    def _handle_free_turn(self, user, game_model, message, request):
        user_spin_object = get_object_or_404(SpinWheel, user=user)
        user_spin_object.spin_available -= 1
        user_spin_object.save()

        game_object = get_object_or_404(game_model, user=user)
        game_object.turn_available += 1
        game_object.save()

        return Response({"message": message}, status=status.HTTP_200_OK)

    def _handle_regular_points(self, user_spin_object, points, request):
        user_spin_object.spin_available -= 1
        user_spin_object.save()

        user_recent_earning = RecentEarnings.objects.create(
            user=request.user, way_to_earn="Spin Wheel", point_earned=points
        )

        user_wallet = get_object_or_404(Wallet, user=request.user)
        user_wallet.points += int(points)
        user_wallet.save()

        return Response({'message': f'{points} points added to your account.'}, status=status.HTTP_200_OK)


# noinspection PyMethodMayBeStatic

class DailyCheckIn(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        user = request.user

        if self._has_already_claimed_today(user):
            return Response({'message': 'You have already claimed the award today.'}, status=400)

        self._add_points_to_wallet(user)
        self._record_earning(user)

        return Response({'message': '50 points added to your account.'}, status=200)

    def _has_already_claimed_today(self, user):
        last_claimed = RecentEarnings.objects.filter(user=user, way_to_earn='Daily Check-In').order_by(
            '-created_at').first()
        return last_claimed and last_claimed.created_at == timezone.now().date()

    def _add_points_to_wallet(self, user):
        user_wallet = get_object_or_404(Wallet, user=user)
        user_wallet.points += 50
        user_wallet.save()

    def _record_earning(self, user):
        RecentEarnings.objects.create(user=user, way_to_earn='Daily Check-In', point_earned=50)


# noinspection PyMethodMayBeStatic
class WalletView(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        user = request.user

        user_wallet = get_object_or_404(Wallet, user=user)

        return Response({'points': user_wallet.points}, status=status.HTTP_200_OK)


# noinspection PyMethodMayBeStatic
class UserSpinTurn(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        user = request.user

        # Get the user's spin wheel object or return a 404 error if it doesn't exist
        spin_wheel = get_object_or_404(SpinWheel, user=user)

        # Check the time since the user's last spin
        last_spin_time = spin_wheel.last_played_at
        current_time = django_timezone.now()
        time_since_last_spin = current_time - last_spin_time

        # If it has been more than 24 hours since the last spin, reset the spin availability to 1
        if time_since_last_spin >= timedelta(hours=24):
            spin_wheel.spin_available = 1
            spin_wheel.save()

        # Return the current spin availability for the user
        return Response({'spin_available': spin_wheel.spin_available}, status=status.HTTP_200_OK)


# noinspection PyMethodMayBeStatic
class UserSpinFree(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        user = request.user

        spin_wheel = get_object_or_404(SpinWheel, user=user)

        spin_wheel.spin_available += 1
        spin_wheel.save()

        return Response({'spin_available': spin_wheel.spin_available}, status=status.HTTP_200_OK)


# noinspection PyMethodMayBeStatic
class UserTTCAvailableTurn(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        user = request.user

        tt_object = get_object_or_404(TickTacToe, user=user)

        last_played_time = tt_object.last_played_at
        current_time = django_timezone.now()
        time_since_last_played = current_time - last_played_time

        if time_since_last_played >= timedelta(hours=6):
            tt_object.turn_available = 10
            tt_object.save()

        return Response({'turn_available': tt_object.turn_available}, status=status.HTTP_200_OK)


# noinspection PyMethodMayBeStatic
class AddUserTTCTurn(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args, **kwargs):
        user = request.user

        tt_object = get_object_or_404(TickTacToe, user=user)
        tt_object.turn_available += 1
        tt_object.save()

        return Response({'message': 'Free Turn Given'}, status=status.HTTP_200_OK)


# noinspection PyMethodMayBeStatic
class TTCApiView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        user = request.user

        # Get the TTC object for the user
        ttc_object = get_object_or_404(TickTacToe, user=user)
        ttc_object.turn_available -= 1
        ttc_object.save()

        # Add entry to recent earnings
        user_recent_earning = RecentEarnings.objects.create(user=user, way_to_earn="Tic Tac Toe", point_earned=5)

        # Add points to the user's wallet
        user_wallet = get_object_or_404(Wallet, user=user)
        user_wallet.points += 5
        user_wallet.save()

        return Response({"message": "Points Added To The Wallet"}, status=status.HTTP_200_OK)


# noinspection PyMethodMayBeStatic
class TTCLoseApi(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        user = request.user

        # Get the TTC object for the user
        ttc_object = get_object_or_404(TickTacToe, user=user)

        if ttc_object.turn_available == 0:
            return Response({"message": "User Lost A Game"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            ttc_object.turn_available -= 1
            ttc_object.save()
            return Response({"message": "User Lost A Game"}, status=status.HTTP_400_BAD_REQUEST)


# noinspection PyMethodMayBeStatic
class MonsterHunterTurn(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        user = request.user

        # Get the MonsterHunter object for the user
        monster_hunter_object = get_object_or_404(MonsterHunter, user=user)

        last_played_time = monster_hunter_object.last_played_at
        current_time = django_timezone.now()
        time_since_last_played = current_time - last_played_time

        # Check if it has been more than 12 hours since the last play
        if time_since_last_played >= timedelta(hours=12):
            monster_hunter_object.turn_available = 2
            monster_hunter_object.save()

        return Response({'turn_available': monster_hunter_object.turn_available}, status=status.HTTP_200_OK)


# noinspection PyMethodMayBeStatic
class MonsterHunterApi(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        serializer = MonsterHunterSerializer(data=request.data)
        if serializer.is_valid():
            points = serializer.validated_data['points']

            # Update the user's wallet with the earned points
            user_wallet = Wallet.objects.get(user=request.user)
            user_wallet.points += int(points)
            user_wallet.save()

            # Add entry to recent earnings
            RecentEarnings.objects.create(user=request.user, way_to_earn="Monster Hunter", point_earned=points)

            # Reset the turn availability for Monster Hunter
            MonsterHunter.objects.filter(user=request.user).update(turn_available=0)

            return Response({"message": "Done"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)


# noinspection PyMethodMayBeStatic
class AddMonsterHunterApi(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        # Get the user object of monster hunter
        user_monster_hunter_obj = MonsterHunter.objects.get(user=request.user)
        user_monster_hunter_obj.turn_available += 1
        user_monster_hunter_obj.save()

        return Response({"message": "Done"}, status=status.HTTP_200_OK)


# noinspection PyUnresolvedReferences
class QuizInQuestions(APIView):
    authentication_classes = [TokenAuthentication]
    serializer_class = QuizSerializer

    def post(self, request):
        # Deducting a turn for the user
        user_quiz_obj = Quiz.objects.get(user=request.user)

        if user_quiz_obj.turn_available == 0:
            return Response({"message": "You Have 0 Turns Available"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user_quiz_obj.turn_available -= 1
            user_quiz_obj.save()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subject = serializer.validated_data['subject']

        # Getting the Subject object
        subject_obj = Subject.objects.get(subject=subject)

        # Getting the Questions
        questions = Questions.objects.filter(subject=subject_obj).order_by('?')[:10]

        # Serialize the questions
        serializer = QuestionSerializer(questions, many=True)
        serialized_questions = serializer.data

        # Return the serialized questions as a JSON response
        return Response(serialized_questions, status=status.HTTP_200_OK)


class QuizApi(APIView):
    authentication_classes = [TokenAuthentication]
    serializer_class = QuizApiSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        points = serializer.validated_data['points']

        # Update the user's wallet with the earned points
        user_wallet = Wallet.objects.get(user=request.user)
        user_wallet.points += int(points)
        user_wallet.save()

        # Add entry to recent earnings
        RecentEarnings.objects.create(user=request.user, way_to_earn="Quiz In", point_earned=points)

        return Response({"message": "Done"}, status=status.HTTP_200_OK)


# noinspection PyMethodMayBeStatic,PyUnresolvedReferences
class AddQuizInApi(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        # Get the Quiz object for the authenticated user
        user_quiz_obj = Quiz.objects.get(user=request.user)

        # Deduct a turn for the user
        user_quiz_obj.turn_available += 1
        user_quiz_obj.save()

        return Response({"message": "Done"}, status=status.HTTP_200_OK)


# noinspection PyMethodMayBeStatic
class QuizInTurns(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        user = request.user

        try:
            user_quiz_obj = self.get_user_quiz_object(user)
            turns_available = self.calculate_turns_available(user_quiz_obj)
            return Response({"message": str(turns_available)}, status=status.HTTP_200_OK)

        except Quiz.DoesNotExist:
            return Response({"message": "Quiz object does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"message": "Some Error Occurred"}, status=status.HTTP_400_BAD_REQUEST)

    def get_user_quiz_object(self, user):
        # Retrieve the user's quiz object
        return Quiz.objects.get(user=user)

    def calculate_turns_available(self, quiz_obj):
        # Calculate the turns available based on last played time
        last_played_time = quiz_obj.last_played_at
        current_time = django_timezone.now()
        time_since_last_played = current_time - last_played_time

        if time_since_last_played >= timedelta(hours=6):
            quiz_obj.turn_available = 1
            quiz_obj.save()

        return quiz_obj.turn_available


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
