from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Transaction, Referral

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
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