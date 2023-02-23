import random
import string
from django.db import models
from django.contrib.auth.models import User
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime
# Create your models here.

def generate_unique_code():
    length = 7
    while True:
        code = ''.join(random.choices(string.digits, k=length))
        if Profile.objects.filter(user_code=code).count() == 0:
            break

    return code

def get_random_image_path():
    path = "./media/user_profile_images/"
    images = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    return random.choice(images)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    number = models.CharField(max_length=11, blank=True, null=True)
    user_code = models.CharField(max_length=7, default=generate_unique_code, unique=True, blank=True, null=True)
    profile_pic_path = models.CharField(max_length=255, blank=True, null=True, default=get_random_image_path)
    total_earned = models.CharField(max_length=5000, blank=True, null=True, default="0")

    @receiver(post_save, sender=User)
    def create_profile(sender, instance, created, **kwargs):
        if created:
            Profile.objects.create(user=instance)

    def __str__(self) -> str:
        return self.user.username

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0, null=True, blank=True)

    @receiver(post_save, sender=User)
    def create_profile(sender, instance, created, **kwargs):
        if created:
            Wallet.objects.create(user=instance)

    def add_points(self, points):
        return self.points + points

    def __str__(self) -> str:
        return self.user.username


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0, null=True, blank=True)
    payment_method = models.CharField(max_length=100, default="Easypaisa")
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)


    def check_balance(self):
        current_user_points = Wallet.objects.get(user=self.user).points
        if self.points > current_user_points:
            return False
        else:
            return True
        
    def deduct_balance(self):
        current_user_points = Wallet.objects.get(user=self.user).points
        current_user_points -= self.points



    def __str__(self) -> str:
        return f"{self.user.username} made transaction of {self.points} points in {self.payment_method}"
    
class RecentEarnings(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    way_to_earn = models.CharField(max_length=300, blank=True, null=True)
    point_earned = models.IntegerField(blank=True, null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)


class Referral(models.Model):
    user = models.OneToOneField(Profile, on_delete=models.CASCADE)
    code  = models.CharField(max_length=7, null=True, blank=True)

    def check_code(self):
        if (Profile.objects.get(user_code=self.code)).exits():
            self.add_points_to_referrer()
            return True
        else:
            return False

   
    def __str__(self) -> str:
        referred_user = self.user.user.username
        referred_by = Profile.objects.get(user_code=self.code).user.username
        return f"The user {referred_user} was refferd by the user {referred_by}"


