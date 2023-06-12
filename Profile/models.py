import random
import string
from django.db import models
from django.contrib.auth.models import User
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.utils import timezone

# Create your models here.

def generate_unique_code():
    length = 7
    while True:
        code = ''.join(random.choices(string.digits, k=length))
        if Profile.objects.filter(user_code=code).count() == 0:
            break
    return code


def generate_username(email):
    # Get the username from the email by removing the domain name
    username = email.split('@')[0]

    # Check if the username is already taken
    if User.objects.filter(username=username).exists():
        # If the username is taken, add a random string at the end to make it unique
        username += '_' + get_random_string(length=5)

    return username

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=500, blank=True, null=True)
    new_user = models.BooleanField(default=True)
    dob = models.CharField(max_length=50, default="Click Here To Add")
    country = models.CharField(max_length=200, default="United States", blank=True, null=True)
    number = models.CharField(max_length=500, blank=True, null=True, default="Click Here To Add")
    user_code = models.CharField(max_length=7, default=generate_unique_code, unique=True, blank=True, null=True)
    profile_pic_path = models.CharField(max_length=1000, blank=True, null=True, default=1)

    @receiver(post_save, sender=User)
    def create_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    def __str__(self) -> str:
        return self.user.username

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)

    @receiver(post_save, sender=User)
    def create_profile(sender, instance, created, **kwargs):
        if created:
            Wallet.objects.create(user=instance)

    def __str__(self) -> str:
        return self.user.username


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0, null=True, blank=True)
    address = models.CharField(max_length=500, default="")
    completed = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=100, default="Easypaisa")
    created_at = models.DateField(default=timezone.now().date())

    def __str__(self) -> str:
        return f"{self.user.username} made a transaction of {self.points} points via {self.payment_method}"

class RecentEarnings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    way_to_earn = models.CharField(max_length=300, blank=True, null=True)
    point_earned = models.IntegerField(blank=True, null=True, default=0)
    created_at = models.DateField(default=timezone.now().date())

    def __str__(self) -> str:
        return f"{self.user.first_name} earned {self.point_earned} through {self.way_to_earn}"
     

class Referral(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE)
    code = models.CharField(max_length=7, null=True, blank=True)
    signed_up_at = models.DateField(default=timezone.now().date())


    def __str__(self) -> str:
        referred_user = self.user.user.username
        referred_by = Profile.objects.get(user_code=self.code).user.username
        return f"The user {referred_user} was referred by the user {referred_by} at {self.signed_up_at}"

class ResetPassword(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pin = models.CharField(max_length=4, null=False, blank=False, default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.username} requested pin that is {self.pin}"

class SocialAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.username} created account using google"
    

class HelpCenter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=1000)
    message = models.CharField(max_length=10000)
    