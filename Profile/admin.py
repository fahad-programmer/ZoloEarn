from django.contrib import admin
from .models import HelpCenter, Profile, Wallet, Transaction, Referral, RecentEarnings, ResetPassword, SocialAccount

# Register your models here.
admin.site.register(Profile)
admin.site.register(Wallet)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'points', 'payment_method', 'completed']
    list_filter = ['completed']

admin.site.register(Transaction, TransactionAdmin)


admin.site.register(Referral)
admin.site.register(RecentEarnings)
admin.site.register(ResetPassword)
admin.site.register(SocialAccount)
admin.site.register(HelpCenter)
