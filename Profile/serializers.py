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