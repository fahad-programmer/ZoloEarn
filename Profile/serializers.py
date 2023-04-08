from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Transaction, Referral
from .models import generate_username

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
        fields = ('id', 'points', 'payment_method')

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
    pin  = serializers.CharField(max_length=7)