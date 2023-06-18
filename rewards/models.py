from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save

# Create your models here.

class SpinWheel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    spin_available = models.IntegerField(default=2)
    last_played_at = models.DateTimeField(auto_now=True)

    @receiver(post_save, sender=User)
    def createGameInstance(sender, instance, created, **kwargs):
        if created:
            SpinWheel.objects.create(user=instance)

    def __str__(self) -> str:
        return self.user.first_name

class MonsterHunter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    turn_available = models.IntegerField(default=2)
    last_played_at = models.DateTimeField(auto_now=True)

    @receiver(post_save, sender=User)
    def createGameInstance(sender, instance, created, **kwargs):
        if created:
            MonsterHunter.objects.create(user=instance)

    def __str__(self) -> str:
        return self.user.first_name

    

class TickTacToe(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    turn_available = models.IntegerField(default=10)
    last_played_at = models.DateTimeField(auto_now=True)

    @receiver(post_save, sender=User)
    def createGameInstance(sender, instance, created, **kwargs):
        if created:
            TickTacToe.objects.create(user=instance)

    def __str__(self) -> str:
        return self.user.first_name


class Quiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    turn_available = models.IntegerField(default=1)
    last_played_at = models.DateTimeField(auto_now=True)

    @receiver(post_save, sender=User)
    def createGameInstance(sender, instance, created, **kwargs):
        if created:
            Quiz.objects.create(user=instance)

    def __str__(self) -> str:
        return self.user.username


class Subject(models.Model):
    subject = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.subject
    


class Questions(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    question = models.CharField(max_length=500)
    choice1 = models.CharField(max_length=200)
    choice2 = models.CharField(max_length=200)
    choice3 = models.CharField(max_length=200)
    choice4 = models.CharField(max_length=200)
    answer = models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.question
