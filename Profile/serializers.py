from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Transaction, Referral, ResetPassword, RecentEarnings
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
        fields = ('address', 'points', 'payment_method')

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
    rank = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['first_name', 'wallet_points', 'profile_pic_path', 'rank']

    def get_rank(self, obj):
        # Get the rank of the user based on their wallet points
        users = User.objects.order_by('-wallet__points')
        user_ids = [user.id for user in users]
        rank = user_ids.index(obj.id) + 1
        return rank


class ProfileImageSerializer(serializers.ModelSerializer):
    profile_pic_name = serializers.CharField(max_length=1000)

    class Meta:
        model = Profile
        fields = ["profile_pic_name"]

class PaymentInfoSerializer(serializers.Serializer):
    currencyInfo = serializers.CharField(max_length=100)
    currencyRate = serializers.IntegerField()
    
class ProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', required=False)
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.CharField(source='user.email', required=False)

    class Meta:
        model = Profile
        fields = ["email",'number', 'first_name', 'dob', 'country', 'username', 'profile_pic_path']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        instance.user.first_name = user_data.get('first_name', instance.user.first_name)
        instance.user.username = user_data.get('username', instance.user.username)
        instance.user.save()

        return super().update(instance, validated_data)


class RecentEarningsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecentEarnings
        fields = ('way_to_earn', 'point_earned', 'created_at')
