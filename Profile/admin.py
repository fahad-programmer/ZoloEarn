from django.contrib import admin
from .models import Profile, Wallet, Transaction, Referral, RecentEarnings, ResetPassword

# Register your models here.
admin.site.register(Profile)
admin.site.register(Wallet)
admin.site.register(Transaction)
admin.site.register(Referral)
admin.site.register(RecentEarnings)
admin.site.register(ResetPassword)
