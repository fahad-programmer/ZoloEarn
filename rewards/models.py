from django.db import models
from django.contrib.auth.models import User
from django.db.models import CharField, Q
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone


# Create your models here.

# noinspection PyMethodParameters,PyUnresolvedReferences
class SpinWheel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    spin_available = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(5)])
    last_played_at = models.DateTimeField(auto_now=True)

    @receiver(post_save, sender=User)
    def createGameInstance(sender, instance, created, **kwargs):
        if created:
            SpinWheel.objects.create(user=instance)

    def __str__(self) -> str:
        return self.user.first_name


class MonsterHunter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    turn_available = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(5)])
    last_played_at = models.DateTimeField(auto_now=True)

    @receiver(post_save, sender=User)
    def createGameInstance(sender, instance, created, **kwargs):
        if created:
            MonsterHunter.objects.create(user=instance)

    def __str__(self) -> str:
        return self.user.first_name


class TickTacToe(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    turn_available = models.PositiveIntegerField(default=10, validators=[MinValueValidator(0), MaxValueValidator(20)])
    last_played_at = models.DateTimeField(auto_now=True)

    @receiver(post_save, sender=User)
    def createGameInstance(sender, instance, created, **kwargs):
        if created:
            TickTacToe.objects.create(user=instance)

    def __str__(self) -> str:
        return self.user.first_name


class Quiz(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    turn_available = models.PositiveIntegerField(default=1, validators=[MinValueValidator(0), MaxValueValidator(5)])
    last_played_at = models.DateTimeField(auto_now=True)

    @receiver(post_save, sender=User)
    def createGameInstance(sender, instance, created, **kwargs):
        if created:
            Quiz.objects.create(user=instance)

    def __str__(self) -> str:
        return self.user.username


class Subject(models.Model):
    subject = models.CharField(max_length=100)

    def __str__(self) -> CharField:
        return self.subject


class Questions(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    question = models.CharField(max_length=500)
    choice1 = models.CharField(max_length=200)
    choice2 = models.CharField(max_length=200)
    choice3 = models.CharField(max_length=200)
    choice4 = models.CharField(max_length=200)
    answer = models.CharField(max_length=200)

    def __str__(self) -> CharField:
        return self.question


class ZoloVideos(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    videos_watched = models.PositiveIntegerField(default=50, validators=[MinValueValidator(0), MaxValueValidator(50)])
    last_watched = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    @receiver(post_save, sender=User)
    def createGameInstance(sender, instance, created, **kwargs):
        if created:
            ZoloVideos.objects.create(user=instance)

    def get_remaining_reset_time(self):
        if self.videos_watched == 0 and self.last_watched <= timezone.now() - timezone.timedelta(hours=24):
            # Videos have been reset, so no time remaining until the next reset
            return timezone.timedelta()

        # Calculate the time remaining until the next reset
        reset_time = self.last_watched + timezone.timedelta(hours=24)
        remaining_time = reset_time - timezone.now()
        return remaining_time

    def get_videos_by_country(self):
        remaining_reset_time = self.get_remaining_reset_time()

        if self.videos_watched == 0 and remaining_reset_time == timezone.timedelta():
            print(remaining_reset_time)
            # Reset the videos_watched count to the default value (50)
            self.videos_watched = 50
            # Set the last_watched time to the current time since the videos have been reset
            self.last_watched = timezone.now()
            self.save()
        else:
            pass

        available_videos = 50 - self.videos_watched

        # Handling the edge case that it is never zero

        if available_videos < 0:
            available_videos = 0

        country = self.user.profile.country
        videos = Videos.objects.filter(
            Q(country=country)
        ).values_list('videos', flat=True)

        if not videos:
            videos = Videos.objects.filter(
                Q(country="United States")
            ).values_list('videos', flat=True)

        if videos:
            videos = [url for video in videos for url in video.split(',')][available_videos:]
        else:
            videos = []

        return videos


class Videos(models.Model):
    country = models.CharField(max_length=150)
    videos = models.TextField()

    def __str__(self):
        return self.country


class Articles(models.Model):
    """The Main Model That Will Consists OF The Article"""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=500, default="None")
    country = models.CharField(max_length=150)
    banner_image_url = models.CharField(max_length=1000)
    meta_description = models.CharField(max_length=700)
    article_body = models.TextField()

    def __str__(self):
        return self.title


class ZoloArticles(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    articles_read = models.PositiveIntegerField(default=50, validators=[MinValueValidator(0), MaxValueValidator(50)])
    last_read = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username

    @receiver(post_save, sender=User)
    def createGameInstance(sender, instance, created, **kwargs):
        if created:
            ZoloArticles.objects.create(user=instance)

    def get_remaining_reset_time(self):
        if self.articles_read == 0 and self.last_read <= timezone.now() - timezone.timedelta(hours=24):
            # Videos have been reset, so no time remaining until the next reset
            return timezone.timedelta()

        # Calculate the time remaining until the next reset
        reset_time = self.last_read + timezone.timedelta(hours=24)
        remaining_time = reset_time - timezone.now()
        return remaining_time

    def get_user_articles(self):
        remaining_reset_time = self.get_remaining_reset_time()

        if self.articles_read == 0 and remaining_reset_time == timezone.timedelta():
            # Reset the articles_read count to the default value (20)
            self.articles_read = 50
            # Set the last_read time to the current time since the articles have been reset
            self.last_read = timezone.now()
            self.save()
        else:
            pass

        available_articles = 50 - self.articles_read

        if available_articles < 0:
            available_articles = 0

        articles = Articles.objects.all().values('id', 'title', 'banner_image_url', 'meta_description')[available_articles:]

        return articles
