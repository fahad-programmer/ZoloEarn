from django.contrib import admin
from .models import SpinWheel, TickTacToe, MonsterHunter, Quiz, Questions, Subject, ZoloVideos, Videos


# Register your models here.

class SpinWheelModel(admin.ModelAdmin):
    search_fields = ['user__username']


admin.site.register(SpinWheel, SpinWheelModel)

admin.site.register(TickTacToe)
admin.site.register(MonsterHunter)
admin.site.register(Questions)
admin.site.register(Quiz)
admin.site.register(Subject)


class ZoloVideolModel(admin.ModelAdmin):
    search_fields = ['user__username']


admin.site.register(ZoloVideos, ZoloVideolModel)

admin.site.register(Videos)
