from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import CreateTransactionSerializer, HelpCenterSerializer, PaymentInfoSerializer, ProfileSerializer, RecentEarningsSerializer, UserSerializer, TransactionSerializer, ReferralSerializer, GetReferralSerializer,  ForgotPasswordSerializer, ForgotPasswordCheckPinSerializer, UserResetPassword, SocialAccountSerializer, VerificationPinSerializer, generate_username, UserStatsSerializer, ProfileImageSerializer
from .models import HelpCenter, ResetPassword, Transaction, Referral, Wallet, Profile, RecentEarnings, SocialAccount, VerifyUser
from django.contrib.auth import authenticate, get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.core.exceptions import ValidationError
from rest_framework import viewsets
from django_email_verification import send_email
from rest_framework.views import APIView
from rest_framework import generics
from django.core.mail import EmailMessage
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.template.loader import render_to_string
from django.db.models import Sum
from django.http import JsonResponse

# Store the last time an email was sent in a dictionary
last_email_sent = {}

User = get_user_model()

ALLOWED_EMAIL_PROVIDERS = ["tutanota.com", "protonmail.com", "zoho.com", "hubspot.com", "mail.com", "gmx.com", "yandex.com",
                           "pm.com", 'gmail.com', 'yahoo.com', 'icloud.com', "outlook.com", "hotmail.com", "aol.com", "aim.com", "titan.email"]


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
                return Response({"message": "Signups from this email provider are not allowed."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Return an error response if email is not provided
            return Response({"message": "Please provide an email address."}, status=status.HTTP_400_BAD_REQUEST)

        # Checking Profile Database for the device id
        check_profile_data = Profile.objects.filter(device_id=device_id)
        if len(check_profile_data) == 3:  # If more than 3 accounts found error is returned
            return Response({"message": "No More Accounts Can Be Created On This Device"}, status=status.HTTP_400_BAD_REQUEST)

        # Create a UserSerializer instance with request data
        serializer = self.get_serializer(data=request.data)

        try:
            # Raise a validation error if serializer data is invalid
            serializer.is_valid(raise_exception=True)

            # Check if user with the same email already exists
            if User.objects.filter(email=email).exists():
                # Return an error response if email is already taken
                return Response({"message": "Email already exists."}, status=status.HTTP_400_BAD_REQUEST)

            # Save the newly created user
            self.perform_create(serializer)

            # Get response headers
            headers = self.get_success_headers(serializer.data)

            # Set user as inactive and send an email to activate the account
            user = User.objects.get(pk=serializer.data['id'])
            user.is_active = False
            user.save()
            SendVerificationEmail(user.get_username(), user.email)

            # Save device_id in Profile model
            profile = Profile.objects.get(user=user)
            profile.device_id = device_id
            profile.country = country
            profile.save()

        except ValidationError:
            # Return an error response if serializer data is invalid
            return Response({"message": "Invalid data. Please check your input."})

        # Generate a token for the newly created user
        user = User.objects.get(pk=serializer.data['id'])
        token, created = Token.objects.get_or_create(user=user)

        # Return the token in the response
        return Response({'token': token.key, "message": "Account created."}, status=status.HTTP_201_CREATED, headers=headers)

    def login(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            if user.is_active:
                return Response({'token': token.key, "message": "verified"})
            else:
                return Response({"message": "non-verified", "token": token.key}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        else:
            return Response({"message": "Username Or Password Is Incorrect"}, status=status.HTTP_400_BAD_REQUEST)



def SendVerificationEmail(username, email):
    # Deleting all the objects that are old than 15 mins
    VerifyUser.objects.filter(
        created_at__lte=timezone.now() - timezone.timedelta(minutes=15)).delete()

    # Check if there is an existing VerifyUser object for the user
    verify_user = VerifyUser.objects.filter(
        user=User.objects.get(username=username)).first()

    # If there is an existing VerifyUser object and it was created less than 15 minutes ago, return an error
    if verify_user and timezone.now() < verify_user.created_at + timezone.timedelta(minutes=15):
        time_diff = (verify_user.created_at +
                     timezone.timedelta(minutes=5) - timezone.now()).seconds // 60
        return Response({'message': f'Please wait {time_diff} minutes before requesting a new PIN.'}, status=status.HTTP_400_BAD_REQUEST)

    # Generate a new PIN and create a new ResetPassword object for the user
    pin = get_random_string(length=4, allowed_chars='1234567890')
    verify_user_object = VerifyUser.objects.create(
        user=User.objects.get(username=username), pin=pin)
    verify_user_object.save()

    # Sending the Email

    context = {"username": User.objects.get(email=email).username, "pin": pin}
    email_body = render_to_string('mail/verifyUser.html', context)

    email = EmailMessage(
        'Complete Your Signup On ZoloEarn',
        email_body,
        'zoloearn.llc@gmail.com',
        to=[email]
    )

    email.content_subtype = 'html'
    email.send()

class CheckVerificationPin(APIView):
    def post(self, request, format=None):
        serializer = VerificationPinSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({'message': 'User with this email does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

            pin = serializer.validated_data['pin']
            try:
                verify_pin_obj = VerifyUser.objects.get(user=user)
                if verify_pin_obj.pin == pin and timezone.now() <= verify_pin_obj.created_at + timezone.timedelta(minutes=5):
                    return Response({'message': 'Pin verified successfully'}, status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'Invalid or expired PIN'}, status=status.HTTP_400_BAD_REQUEST)
            except ResetPassword.DoesNotExist:
                return Response({'message': 'No reset password request found for this user.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class TransactionListView(generics.ListAPIView):
    authentication_classes = [TokenAuthentication]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        user = self.request.user
        return Transaction.objects.filter(user=user)
    

class AppRating(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request, *args):
        user_wallet = Wallet.objects.get(user=request.user)
        user_wallet.points += 30

        # Adding entry to recent earnings
        user_recent_earning = RecentEarnings.objects.create(user=request.user, way_to_earn="App Rating", point_earned=30)
        user_recent_earning.save()

        return Response({"message": "Done"}, status=status.HTTP_200_OK)


        


class ReferralView(APIView):
    authentication_classes = [TokenAuthentication]
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
                Referral.objects.get(
                    user=Profile.objects.get(user=current_user))
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
            referred_user_wallet.points += 25
            referred_user_wallet.save()

            #Writing the earning history from database
            referrerd_earning = RecentEarnings.objects.create(user=referred_user, way_to_earn="Referral Points", point_earned=25)
            referrerd_earning.save()

            return Response({"message": "Referral successful"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






class CheckUserActive(APIView):
    def get(self, request, token, format=None):
        try:
            token_obj = get_object_or_404(Token, key=token)
            user = token_obj.user
        except Token.DoesNotExist:
            return Response({'message': 'No User Account'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_active:
            return Response({'message': 'User is active.', 'email': user.email}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'User is not active.'}, status=status.HTTP_200_OK)


class UserCodeAPIView(APIView):

    # Getting this User Refferal Code
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

    # Getting the list of Refferal For the User
    authentication_classes = [TokenAuthentication]

    def get(self, request, format=None):
        referrals = Referral.objects.filter(
            code=request.user.profile.user_code)
        serializer = GetReferralSerializer(referrals, many=True)
        return Response(serializer.data)





class ForgotPasswordView(APIView):
    def post(self, request, format=None):

        # Deleting all the objects that are old than 15 mins
        ResetPassword.objects.filter(
            created_at__lte=timezone.now() - timezone.timedelta(minutes=15)).delete()

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
                time_diff = (reset_password.created_at +
                             timezone.timedelta(minutes=15) - timezone.now()).seconds // 60
                return Response({'message': f'Please wait {time_diff} minutes before requesting a new PIN.'}, status=status.HTTP_400_BAD_REQUEST)

            # Generate a new PIN and create a new ResetPassword object for the user
            pin = get_random_string(length=4, allowed_chars='1234567890')
            reset_password_object = ResetPassword.objects.create(
                user=user, pin=pin)
            reset_password_object.save()

            # Sending the Email

            context = {"username": User.objects.get(
                email=email).username, "pin": pin}
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

        # Setting the password and validating the inputs
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            # Setting the user password
            get_user = User.objects.get(email=email)
            get_user.set_password(password)
            get_user.save()

            # Sending email to the user
            context = {"username": User.objects.get(email=email).username}
            email_body = render_to_string(
                'mail/password_change_notification.html', context)

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
            return Response({"message": "Email Already Exists In Database"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Checking Profile Database for the device id
            check_profile_data = Profile.objects.filter(device_id=device_id)
            if len(check_profile_data) == 3:  # If more than 3 accounts found error is returned
                return Response({"message": "No More Accounts Can Be Created On This Device"}, status=status.HTTP_400_BAD_REQUEST)

            # First creating the simple User object and generating a username
            userObjectUsername = generate_username(email=email)
            userObject = User.objects.create(
                email=email, first_name=first_name, username=userObjectUsername)
            userObject.save()

            # Save device_id in Profile model
            profile = Profile.objects.get(user=userObject)
            profile.device_id = device_id
            profile.country = country
            profile.save()

            # Now Creating a social account
            userObjectSocialAccount = SocialAccount.objects.create(
                user=userObject)
            userObjectSocialAccount.save()

            # Generating token for user
            token, created = Token.objects.get_or_create(user=userObject)

            return Response({"token": token.key, "message": "Account Created"}, status=status.HTTP_200_OK)

    def login(self, request, format=None):

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Getting email
            email = serializer.validated_data["email"]

            userObject = User.objects.filter(email=email).first()
            userSocialObject = SocialAccount.objects.filter(user=userObject)

            if userObject:
                if userSocialObject.exists():
                    # Generating user for user
                    token, created = Token.objects.get_or_create(
                        user=userObject)
                    return Response({"token": token.key, "message": "Account Logged In"}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Login Through Email And Password"}, status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response({"message": "No Account Found In Database"}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"message": "Some Error Occured"}, status=status.HTTP_400_BAD_REQUEST)


class UserStatsAPIView(generics.ListAPIView):
    serializer_class = UserStatsSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return User.objects.order_by('-wallet__points')[:50]


class ProfileImageSelector(APIView):
    authentication_classes = [TokenAuthentication]
    serializer_class = ProfileImageSerializer

    def post(self, request, *args, **kwargs):

        # Getting the user profile
        get_profile_user = Profile.objects.get(user=request.user)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            # The image Path
            image_path = serializer.validated_data["profile_pic_name"]
            get_profile_user.profile_pic_path = image_path
            get_profile_user.save()

            return Response({"message": "Profile Pic Succesfully Selected"}, status=status.HTTP_200_OK)

        else:
            return Response({"message": "Some Error Occured Try Again Later"}, status=status.HTTP_400_BAD_REQUEST)


class AvailablePaymentMethods(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request, *args):
        # gets the current user
        current_user = request.user

        # gets the current user country
        current_user_country = Profile.objects.get(user=current_user)

        # Payment methods according to the country
        if current_user_country.country == "Pakistan":
            available_payment_methods = ["Easypaisa", "Jazzcash", "Sadapay"]
            return Response({"methods": available_payment_methods}, status=status.HTTP_200_OK)
        elif current_user_country.country == "India":
            available_payment_methods = ["Paytm", "Paypal", "Bitcoin"]
            return Response({"methods": available_payment_methods}, status=status.HTTP_200_OK)
        else:
            available_payment_methods = ["Paypal", "Bitcoin", "Google Pay"]
            return Response({"methods": available_payment_methods}, status=status.HTTP_200_OK)

        return Response({"message": "Some Error Ocuured"}, status=status.HTTP_400_BAD_REQUEST)


class PaymentInfo(APIView):
    authentication_classes = [TokenAuthentication]
    serializer_class = PaymentInfoSerializer

    def get(self, request, *args):
        # gets the current user
        current_user = request.user

        # gets the current user country
        current_user_country = Profile.objects.get(user=current_user)

        # Getting user currecny info and rate
        if current_user_country.country == "Pakistan":
            currencyInfo = "USD - PKR"
            currencyRate = 286
        elif current_user_country.country == "India":
            currencyInfo = "USD - INR"
            currencyRate = 81
        elif current_user_country.country == "Russia":
            currencyInfo = "USD - RUB"
            currencyRate = 84
        else:
            currencyInfo = "USD - USD"
            currencyRate = 1

        serializer = PaymentInfoSerializer(
            {"currencyInfo": currencyInfo, "currencyRate": currencyRate})
        return Response(serializer.data)


class ProfileAPIView(APIView):

    authentication_classes = [TokenAuthentication]

    def get(self, request, *args, **kwargs):
        user = request.user
        profile = Profile.objects.get(user=user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        user = request.user
        profile = Profile.objects.get(user=user)

        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionCreateView(APIView):
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        serializer = CreateTransactionSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            # Check if user has sufficient points

            # get the user wallet and check if he has points
            userWallet = Wallet.objects.get(user=user)
            userAmount = serializer.validated_data['points']

            # Minimum Withdraw points
            minimum_points = 8000

            # get the user profile to check if the user is new
            userProfile = Profile.objects.get(user=user)

            if userProfile.new_user:
                if userWallet.points >= userAmount:
                    if userAmount >= 5000:
                        userWallet.points -= userAmount
                        # Set new user to false
                        userProfile.new_user = False
                        userProfile.save()
                        # Deduct the points from wallet
                        userWallet.save()
                        # Create the transaction object
                        serializer.save(user=user)
                        return Response({"message": "Withdrawal Successful"}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Not Enough Points In Wallet"}, status=status.HTTP_400_BAD_REQUEST)

            else:
                if userWallet.points >= userAmount:
                    if userAmount >= minimum_points:
                        # Deduct the points from wallet
                        userWallet.points -= userAmount
                        userWallet.save()
                        # Create the transaction object
                        serializer.save(user=user)
                        return Response({"message": "Withdrawal Successful"}, status=status.HTTP_200_OK)
                    else:
                        return Response({"message": "Points Less Than Minimum Withdraw (Changes Made Recently)"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"message": "Not Enough Points In Wallet"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecentEarningsView(APIView):
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        user = request.user
        recent_earnings = RecentEarnings.objects.filter(
            user=user).order_by('-created_at')[:10][::-1]
        serializer = RecentEarningsSerializer(recent_earnings, many=True)
        return Response(serializer.data)


class UpdatePasswordView(APIView):
    authentication_classes = [TokenAuthentication]

    def put(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        # Check if the current password is valid
        if not user.check_password(current_password):
            return Response({'message': 'Invalid current password.'}, status=400)

        # Check if the new password and confirm password match
        if new_password != confirm_password:
            return Response({'message': 'New password and confirm password do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        # Update the user's password
        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password updated successfully.'}, status=status.HTTP_200_OK)


class HelpCenterAPIView(APIView):

    authentication_classes = [TokenAuthentication]

    def post(self, request):
        user = request.user
        # Check if the user already has an instance of HelpCenter
        if HelpCenter.objects.filter(user=user).exists():
            return Response({"message": "You can only have one instance of HelpCenter."}, status=status.HTTP_400_BAD_REQUEST)

        # Create a new HelpCenter instance
        serializer = HelpCenterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response({"message": "Submitted Successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VersionCheck(APIView):
    def get(self, request, *args, **kwargs):
        latest_version = "2.3"
        return Response({"message": latest_version})



class GetReferralInfoAPI(APIView):
    # Getting the list of Referrals for the User
    authentication_classes = [TokenAuthentication]

    def get(self, request, format=None):
        user_code = request.user.profile.user_code

        referrals = Referral.objects.filter(code=user_code)
        referral_data = []

        for referral in referrals:
            referred_user = referral.user.user.username
            wallet = Wallet.objects.get(user=referral.user.user)
            referred_wallet_points = wallet.points

            referral_data.append({'referred_user': referred_user, 'wallet_points': referred_wallet_points})

        return Response(referral_data)