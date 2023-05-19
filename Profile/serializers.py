from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Transaction, Referral, ResetPassword
from .models import generate_username, Profile

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'email', 'password', 'username')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        email = validated_data['email']
        username = generate_username(email)
        validated_data['username'] = username
        user = User.objects.create_user(**validated_data)
        return user
    

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('points', 'payment_method', 'created_at', 'completed')

class CreateTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('points', 'payment_method')

class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = ('code',)


class GetReferralSerializer(serializers.ModelSerializer):
    referred_user = serializers.CharField(source='user.user.username')
    signed_up_at = serializers.DateField()

    class Meta:
        model = Referral
        fields = ['referred_user', 'signed_up_at']
        read_only_fields = ['referred_user', 'signed_up_at']



class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ForgotPasswordCheckPinSerializer(serializers.Serializer):
    email = serializers.EmailField()
    pin = serializers.CharField(max_length=4)


class UserResetPassword(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=32)


class SocialAccountSerializer(serializers.Serializer):
    email =  serializers.EmailField()
    first_name = serializers.CharField(max_length=50)
    device_id = serializers.CharField(max_length=500)
    country = serializers.CharField(max_length=200)
    

class UserStatsSerializer(serializers.ModelSerializer):
    wallet_points = serializers.IntegerField(source='wallet.points')
    profile_pic_path = serializers.CharField(source='profile.profile_pic_path')
    rank = serializers.IntegerField(source='user_rank', read_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'wallet_points', 'profile_pic_path', 'rank']


class ProfileImageSerializer(serializers.ModelSerializer):
    profile_pic_name = serializers.CharField(max_length=1000)

    class Meta:
        model = Profile
        fields = ["profile_pic_name"]

class PaymentInfoSerializer(serializers.Serializer):
    currencyInfo = serializers.CharField(max_length=100)
    currencyRate = serializers.IntegerField()
    
class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = ['number', 'first_name', 'dob', 'country', 'username']

    def get_first_name(self, obj):
        return obj.user.first_name
    
    def get_username(self, obj):
        return obj.user.username

    def update(self, instance, validated_data):
        # Update the fields of the Profile model
        instance.number = validated_data.get('number', instance.number)
        instance.dob = validated_data.get('dob', instance.dob)
        instance.save()

        # Update the related User model
        user = instance.user
        user.first_name = validated_data.get('first_name', user.first_name)
        user.save()

        return instance
