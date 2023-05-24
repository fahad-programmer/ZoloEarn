from django.urls import path
from rest_framework import routers
from . import views

urlpatterns = [
    # User Signup
    path('users-signup', views.UserViewSet.as_view({
        'post': 'create'
    })),

    # User Login
    path('users-login', views.UserViewSet.as_view({
        'post': 'login'
    })),

    # User Transactions
    path('user-transactions', views.TransactionListView.as_view(), name="view-transactions"),

    # Referral
    path('referral', views.ReferralView.as_view()),

    # Resend Verification Email
    path('resend-verification-email', views.ResendVerificationEmail.as_view(), name='resend-verification-email'),

    # Check User Active
    path('check-user-active/<str:token>', views.CheckUserActive.as_view(), name="check-user-active"),

    # Get Referrals
    path('get-refferals', views.ReferralList.as_view(), name="refferal-users"),

    # Get User Code
    path('get-user-code', views.UserCodeAPIView.as_view(), name="userCode"),

    # Password Reset
    path('password-reset', views.ForgotPasswordView.as_view()),

    # Password Reset PIN Verify
    path('password-reset-pin-verify', views.CheckForgotPasswordPin.as_view()),

    # Reset Password Complete
    path('reset-password-complete', views.UserResetPasswordView.as_view(), name="password-forget-complete"),

    # Social Authentication Links
    path('users-social-signup', views.SocialAccountApi.as_view({
        'post': 'create'
    })),

    # Social Login
    path('users-social-login', views.SocialAccountApi.as_view({
        'post': 'login'
    })),

    # User Stats
    path('userStats', views.AllUserStats.as_view()),

    # Profile Image Selector
    path("profile-image-select", views.ProfileImageSelector.as_view()),

    # Available Payment Methods
    path("available-payment-methods", views.AvailablePaymentMethods.as_view(), name="available-payment"),

    # Payment Info
    path("paymentinfo", views.PaymentInfo.as_view(), name="PaymentInfo"),

    #Get the profile info and also update
    path('profile', views.ProfileAPIView.as_view(), name='profile'),

    #Create a transaction
    path('checkout', views.TransactionCreateView.as_view(), name="withdraw"),

    #Get user recent earnings
    path('recent-earnings', views.RecentEarningsView.as_view(), name='recent_earnings'),

    #update the user password
    path('update-password', views.UpdatePasswordView.as_view(), name='update_password'),
]
