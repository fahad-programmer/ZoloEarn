from django.contrib import admin
from .models import HelpCenter, Profile, Wallet, Transaction, Referral, RecentEarnings, ResetPassword, SocialAccount

# Register your models here.
class ProfileAdmin(admin.ModelAdmin):
    search_fields = ['user__username']

admin.site.register(Profile, ProfileAdmin)

class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'points')
    search_fields = ('user__username', 'points')

admin.site.register(Wallet, WalletAdmin)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'points', 'payment_method', 'completed']
    list_filter = ['completed']

admin.site.register(Transaction, TransactionAdmin)


admin.site.register(Referral)

class RecentEarningsAdmin(admin.ModelAdmin):
    list_display = ['user', 'way_to_earn', 'point_earned', 'created_at']
    list_filter = ['user']

admin.site.register(RecentEarnings, RecentEarningsAdmin)
admin.site.register(ResetPassword)
admin.site.register(SocialAccount)
admin.site.register(HelpCenter)
