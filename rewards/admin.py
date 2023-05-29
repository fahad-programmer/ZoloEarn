from django.contrib import admin
from .models import SpinWheel, TickTacToe, MonsterHunter, Quiz, Questions, Subject

# Register your models here.
admin.site.register(SpinWheel)
admin.site.register(TickTacToe)
admin.site.register(MonsterHunter)
admin.site.register(Questions)
admin.site.register(Quiz)
admin.site.register(Subject)