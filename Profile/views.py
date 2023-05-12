from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import UserSerializer, TransactionSerializer, ReferralSerializer, GetReferralSerializer,  ForgotPasswordSerializer, ForgotPasswordCheckPinSerializer, UserResetPassword, SocialAccountSerializer, generate_username, UserStatsSerializer, ProfileImageSerializer
from .models import ResetPassword, Transaction, Referral, Wallet, Profile, RecentEarnings, SocialAccount
from django.contrib.auth import authenticate, get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
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
from django.db.models import Sum
from django.db.models import F, Window
from django.db.models.functions import Rank






# Store the last time an email was sent in a dictionary
last_email_sent = {}

User = get_user_model()

ALLOWED_EMAIL_PROVIDERS = ["tutanota.com","protonmail.com", "zoho.com", "hubspot.com", "mail.com", "gmx.com", "yandex.com","pm.com",'gmail.com', 'yahoo.com', 'icloud.com', "outlook.com", "hotmail.com", "aol.com", "aim.com", "titan.email"]

class UserViewSet(viewsets.ModelViewSet):
    # Get all users
    queryset = User.objects.all()
    # UserSerializer used to serialize/deserialize User objects
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        # Get email and device_id from request data
        email = request.data.get('email')
        device_id = request.data.get('device_id')
        country = request.data.get('country')

        # If email is present, check if it belongs to an allowed provider
        if email:
            domain = email.split('@')[1]
            if domain not in ALLOWED_EMAIL_PROVIDERS:
                # Return an error response if email provider is not allowed
                return Response({"message":"Signups from this email provider are not allowed."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Return an error response if email is not provided
            return Response({"message":"Please provide an email address."}, status=status.HTTP_400_BAD_REQUEST)

        #Checking Profile Database for the device id
        check_profile_data = Profile.objects.filter(device_id=device_id)
        if len(check_profile_data) == 3: #If more than 3 accounts found error is returned
            return Response({"message": "No More Accounts Can Be Created On This Device"}, status=status.HTTP_400_BAD_REQUEST)
        

        # Create a UserSerializer instance with request data
        serializer = self.get_serializer(data=request.data)

        try:
            # Raise a validation error if serializer data is invalid
            serializer.is_valid(raise_exception=True)

            # Check if user with the same email already exists
            if User.objects.filter(email=email).exists():
                # Return an error response if email is already taken
                return Response({"message":"Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

            # Save the newly created user
            self.perform_create(serializer)

            # Get response headers
            headers = self.get_success_headers(serializer.data)

            # Set user as inactive and send an email to activate the account
            user = User.objects.get(pk=serializer.data['id'])
            user.is_active = False
            user.save()
            send_email(user)

            # Save device_id in Profile model
            profile = Profile.objects.get(user=user)
            profile.device_id = device_id
            profile.country = country
            profile.save()
            
        except ValidationError:
            # Return an error response if serializer data is invalid
            return Response({"message":"Invalid data. Please check your input."})

        # Generate a token for the newly created user
        user = User.objects.get(pk=serializer.data['id'])
        token, created = Token.objects.get_or_create(user=user)

        # Return the token in the response
        return Response({'token': token.key, "message":"Account created."}, status=status.HTTP_201_CREATED, headers=headers)


    def login(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            if user.is_active:
                return Response({'token': token.key, "message" : "verified"})
            else:
                return Response({"message": "non-verified", "token":token.key}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        else:
            return Response({"message":"Username Or Password Is Incorrect"},status=status.HTTP_400_BAD_REQUEST)



class TransactionListView(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    serializer_class = TransactionSerializer

    
    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(user=user)
        

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

            return Response({"message": "Password Set Successfully Please Log In"}, status=status.HTTP_200_OK)


class SocialAccountApi(viewsets.ModelViewSet):
    serializer_class = SocialAccountSerializer

    def create(self, request, format=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            first_name = serializer.validated_data['first_name']
            email = serializer.validated_data['email']
            device_id = serializer.validated_data['device_id']
            country = serializer.validated_data['country']
        else:
            return Response({"message": "Some Error Occured"}, status=status.HTTP_400_BAD_REQUEST)
        
        

        userQuerySet = User.objects.filter(email=email)

        if userQuerySet.exists():
            return Response({"message":"Email Already Exists In Database"}, status=status.HTTP_400_BAD_REQUEST)
        else:        
            #Checking Profile Database for the device id
            check_profile_data = Profile.objects.filter(device_id=device_id)
            if len(check_profile_data) == 3: #If more than 3 accounts found error is returned
                return Response({"message": "No More Accounts Can Be Created On This Device"}, status=status.HTTP_400_BAD_REQUEST)             
            
            #First creating the simple User object and generating a username
            userObjectUsername = generate_username(email=email)
            userObject = User.objects.create(email=email, first_name=first_name, username=userObjectUsername)
            userObject.save()
            
            # Save device_id in Profile model
            profile = Profile.objects.get(user=userObject)
            profile.device_id = device_id
            profile.country = country
            profile.save()

            #Now Creating a social account
            userObjectSocialAccount = SocialAccount.objects.create(user=userObject)
            userObjectSocialAccount.save()

            #Generating token for user
            token, created = Token.objects.get_or_create(user=userObject)

            return Response({"token": token.key, "message":"Account Created"}, status=status.HTTP_200_OK)
        
    def login(self, request, format=None):

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            #Getting email
            email = serializer.validated_data["email"]

            userObject = User.objects.filter(email=email).first()
            userSocialObject = SocialAccount.objects.filter(user=userObject)

            if userObject:
                if userSocialObject.exists():
                    #Generating user for user
                    token, created = Token.objects.get_or_create(user=userObject)
                    return Response({"token":token.key, "message":"Account Logged In"}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Login Through Email And Password"}, status=status.HTTP_400_BAD_REQUEST)
                
            else:
                return Response({"message": "No Account Found In Database"}, status=status.HTTP_400_BAD_REQUEST)
            
        else:
            return Response({"message": "Some Error Occured"}, status=status.HTTP_400_BAD_REQUEST)



class AllUserStats(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    serializer_class = UserStatsSerializer

    def get_queryset(self):
        top_users = User.objects.annotate(
            points=Sum('wallet__points'),
            user_rank=Window(
                expression=Rank(),
                order_by=[F('wallet__points').desc(), 'id']
            )
        )[:50]

        return top_users

     
class ProfileImageSelector(APIView):
    authentication_classes = [TokenAuthentication]
    serializer_class = ProfileImageSerializer

    def post(self, request, *args, **kwargs):

        #Getting the user profile 
        get_profile_user = Profile.objects.get(user=request.user)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            #The image Path
            image_path = serializer.validated_data["profile_pic_name"]
            get_profile_user.profile_pic_path = image_path
            get_profile_user.save()

            return Response({"message":"Profile Pic Succesfully Selected"}, status=status.HTTP_200_OK)
        
        else:
            return Response({"message":"Some Error Occured Try Again Later"}, status=status.HTTP_400_BAD_REQUEST)

