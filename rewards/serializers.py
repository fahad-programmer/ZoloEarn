from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Articles

from .models import Questions

User = get_user_model()


class UserStatsSerializer(serializers.ModelSerializer):
    wallet_points = serializers.IntegerField(source='wallet.points')

    class Meta:
        model = User
        fields = ['first_name', 'wallet_points']  # Use a list instead of a string


class MonsterHunterSerializer(serializers.Serializer):
    points = serializers.IntegerField()


class QuizSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=200)


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questions
        fields = ["question", "choice1", "choice2", "choice3", "choice4", "answer"]


class QuizApiSerializer(serializers.Serializer):
    points = serializers.CharField(max_length=5)


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Articles
        exclude = ('meta_description', 'country', 'id')
