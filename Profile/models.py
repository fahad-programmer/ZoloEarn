import random
import string
from django.db import models
from django.contrib.auth.models import User
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
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
    refferal = models.CharField(max_length=7, blank=True, null=True)
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

    def __str__(self) -> str:
        return self.user.username



