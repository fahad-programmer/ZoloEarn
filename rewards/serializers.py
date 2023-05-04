from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserStatsSerializer(serializers.ModelSerializer):
    wallet_points = serializers.IntegerField(source='wallet.points')

    class Meta:
        model = User
        fields = ['first_name', 'wallet_points']  # Use a list instead of a string
