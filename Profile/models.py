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
            self.points += points
            self.save()

    def __str__(self) -> str:
        return self.user.username


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0, null=True, blank=True)
    payment_method = models.CharField(max_length=100, default="Easypaisa")
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def check_balance(self):
        current_user_points = Wallet.objects.get(user=self.user).points
        return current_user_points
        
    def deduct_balance(self):
        current_user_points = self.get_current_user_points()
        current_user_points -= self.points
        wallet = Wallet.objects.get(user=self.user)
        wallet.points = current_user_points
        wallet.save()

    def get_current_user_points(self):
        return Wallet.objects.get(user=self.user).points

    def __str__(self) -> str:
        return f"{self.user.username} made a transaction of {self.points} points via {self.payment_method}"

class RecentEarnings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    way_to_earn = models.CharField(max_length=300, blank=True, null=True)
    point_earned = models.IntegerField(blank=True, null=True, default=0)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

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
    code = models.CharField(max_length=7, null=False, blank=False)
    created_at = models.DateTimeField(default=timezone.now())

    def __str__(self) -> str:
        return f"{self.user.username} requested pin that is {self.code}"

    


#Delete all the note automatically after 15 mins
@receiver(post_save, sender=ResetPassword)
def delete_old_reset_password_instances(**kwargs):
    """
    Deletes all ResetPassword instances from the database that are older than 15 minutes.
     """
    fifteen_minutes_ago = timezone.now() - timezone.timedelta(minutes=15)
    old_instances = ResetPassword.objects.filter(created_at__lt=fifteen_minutes_ago)
    old_instances.delete()