from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import UserSerializer, TransactionSerializer, ReferralSerializer, GetReferralSerializer,  ForgotPasswordSerializer, ForgotPasswordCheckPinSerializer, UserResetPassword
from .models import ResetPassword, Transaction, Referral, Wallet, Profile, RecentEarnings
from django.contrib.auth import authenticate, login, get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from rest_framework import viewsets
from django_email_verification import send_email
from rest_framework.views import APIView
from rest_framework import generics
import time
from django.core.mail import EmailMessage
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.template.loader import render_to_string




# Store the last time an email was sent in a dictionary
last_email_sent = {}

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            if User.objects.filter(email=request.data['email']).exists():
                return Response({"message":"Email Already Exists"}, status=status.HTTP_400_BAD_REQUEST)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            # Set user as active
            user = User.objects.get(pk=serializer.data['id'])
            user.is_active = False
            user.save()
            send_email(user)

        except IntegrityError:
            return Response({"message": "Username or email is already in use"}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError:
            return Response({"message":"Invalid Data Check Your Input Please"})

        # Generate a token for the newly created user
        user = User.objects.get(pk=serializer.data['id'])
        token, created = Token.objects.get_or_create(user=user)

        # Return the token in the response
        return Response({'token': token.key, "message":"Account Created"}, status=status.HTTP_201_CREATED, headers=headers)


    def login(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        token, created = Token.objects.get_or_create(user=user)
        if user is not None:
            if user.is_active:
                return Response({'token': token.key, "message" : "verified"})
            else:
                return Response({"message": "non-verified", "token":token.key}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        else:
            return Response({"message":"Username Or Password Is Incorrect"},status=status.HTTP_400_BAD_REQUEST)



class TransactionListCreateView(generics.ListCreateAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    
    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        points = serializer.validated_data['points']
        payment_method = serializer.validated_data['payment_method']
        transaction = Transaction(user=user, points=points, payment_method=payment_method)
        if transaction.check_balance():
            transaction.save()
            wallet = Wallet.objects.get(user=user)
            wallet.points -= points
            wallet.save()
        else:
            raise ValidationError('Insufficient balance')
        

class ReferralView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Referral.objects.all()
    serializer_class = ReferralSerializer

    def post(self, request, format=None):
        # Deserialize the request data using the ReferralSerializer
        serializer = ReferralSerializer(data=request.data)

        if serializer.is_valid():
            code = serializer.validated_data.get('code')
            current_user = request.user

            # Check if the provided referral code is valid
            try:
                referred_user_profile = Profile.objects.get(user_code=code)
            except Profile.DoesNotExist:
                return Response({"message": "Invalid referral code"}, status=status.HTTP_400_BAD_REQUEST)

            referred_user = referred_user_profile.user

            # Check if the current user is trying to refer themselves
            if referred_user == current_user:
                return Response({"message": "You cannot refer yourself"}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the current user already has a referrer code
            try:
                Referral.objects.get(user=Profile.objects.get(user=current_user))
                return Response({"message": "You already have a referrer code"}, status=status.HTTP_400_BAD_REQUEST)
            except Referral.DoesNotExist:
                pass

            # Add points to the referrer's wallet and create a new referral
            referrer_wallet = Wallet.objects.get(user=current_user)
            Referral.objects.create(user=Profile.objects.get(user=current_user), code=code)
            referrer_wallet.points += 50
            referrer_wallet.save()

            #Writing the earning history from database
            referrer_earning = RecentEarnings.objects.create(user=current_user, way_to_earn="Referral Points", point_earned=50)
            referrer_earning.save()


            # Add points to the referred user's wallet
            referred_user_wallet = Wallet.objects.get(user=referred_user)
            referred_user_wallet.points += 100
            referred_user_wallet.save()

            #Writing the earning history from database
            referrerd_earning = RecentEarnings.objects.create(user=referred_user, way_to_earn="Referral Points", point_earned=50)
            referrerd_earning.save()

           
            return Response({"message": "Referral successful"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmail(APIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return Response({"message": "Your account is already verified."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Check the last time an email was sent to this user
                last_sent_time = last_email_sent.get(email, 0)
                current_time = time.time()
                if current_time - last_sent_time < 60:
                    # Return an error message if an email was sent less than a minute ago
                    return Response({"message": "Please wait at least one minute before requesting another verification email."}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Send the email and update the last sent time
                    send_email(user)
                    last_email_sent[email] = current_time
                    return Response({"message": "Email has been sent successfully."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"message": "User with this email does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        


class CheckUserActive(APIView):

    #Checking for the user active condition
    def get(self, request, token, format=None):
        try:
            token_obj = Token.objects.get(key=token)
            user = token_obj.user
            if user.is_active:
                message = "User is active."
            else:
                message = "User is not active."
            email = user.email
            return Response({'message': message, 'email': email}, status=status.HTTP_200_OK)
        except Token.DoesNotExist:
            message = "Invalid token."
            return Response({'message': message}, status=status.HTTP_400_BAD_REQUEST)
        

class UserCodeAPIView(APIView):

    #Getting this User Refferal Code
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
            user_code = profile.user_code
            return Response({'message': user_code})
        except Profile.DoesNotExist:
            return Response({'message': 'Profile does not exist for this user'})



class ReferralList(APIView):

    #Getting the list of Refferal For the User
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        referrals = Referral.objects.filter(code=request.user.profile.user_code)
        serializer = GetReferralSerializer(referrals, many=True)
        return Response(serializer.data)


class ForgotPasswordView(APIView):
    def post(self, request, format=None):

        #Deleting all the objects that are old than 15 mins
        ResetPassword.objects.filter(created_at__lte=timezone.now() - timezone.timedelta(minutes=15)).delete()

        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'message': 'User with this email does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

            # Check if there is an existing ResetPassword object for the user
            reset_password = ResetPassword.objects.filter(user=user).first()

            # If there is an existing ResetPassword object and it was created less than 15 minutes ago, return an error
            if reset_password and timezone.now() < reset_password.created_at + timezone.timedelta(minutes=15):
                time_diff = (reset_password.created_at + timezone.timedelta(minutes=15) - timezone.now()).seconds // 60
                return Response({'message': f'Please wait {time_diff} minutes before requesting a new PIN.'}, status=status.HTTP_400_BAD_REQUEST)


            # Generate a new PIN and create a new ResetPassword object for the user
            pin = get_random_string(length=4, allowed_chars='1234567890')
            reset_password_object = ResetPassword.objects.create(user=user, pin=pin)
            reset_password_object.save()

            #Sending the Email

            context = {"username" : User.objects.get(email=email).username, "pin": pin}
            email_body = render_to_string('mail/forget_email.html', context)

            email = EmailMessage(
                'Password Reset for Zolo Earn App',
                email_body,
                'zoloearn.llc@gmail.com',
                to=[email]
                )

            email.content_subtype = 'html'
            email.send()

            return Response({'message': 'An email has been sent to you with your password reset PIN.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CheckForgotPasswordPin(APIView):
    def post(self, request, format=None):
        serializer = ForgotPasswordCheckPinSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'message': 'User with this email does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

            pin = serializer.validated_data['pin']
            try:
                reset_password_obj = ResetPassword.objects.get(user=user)
                if reset_password_obj.pin == pin and timezone.now() <= reset_password_obj.created_at + timezone.timedelta(minutes=15):
                    return Response({'message': 'Pin verified successfully'}, status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'Invalid or expired PIN'}, status=status.HTTP_400_BAD_REQUEST)
            except ResetPassword.DoesNotExist:
                return Response({'message': 'No reset password request found for this user.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserResetPasswordView(APIView):
    def post(self, request, format=None):
        serializer = UserResetPassword(data=request.data)


        #Setting the password and validating the inputs
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            #Setting the user password
            get_user = User.objects.get(email=email)
            get_user.set_password(password)
            get_user.save()


            #Sending email to the user
            context = {"username" : User.objects.get(email=email).username}
            email_body = render_to_string('mail/password_change_notification.html', context)

            email = EmailMessage(
                'Password Reset Succesful',
                email_body,
                'zoloearn.llc@gmail.com',
                to=[email]
                )

            email.content_subtype = 'html'
            email.send()



            Response({"message", "Password Set Successfully Please Log In"}, status=status.HTTP_200_OK)


