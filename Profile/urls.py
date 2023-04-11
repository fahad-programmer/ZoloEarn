from django.urls import path
from rest_framework import routers
from . import views



urlpatterns = [
    path('users-signup', views.UserViewSet.as_view({
        'post': 'create'
    })),
    path('users-login', views.UserViewSet.as_view({
        'post': 'login'
    })),
    path('transaction', views.TransactionListCreateView.as_view(), name="create-transaction"),
    path('referral', views.ReferralView.as_view()),
    path('resend-verification-email', views.ResendVerificationEmail.as_view(), name='resend-verification-email'),
    path('check-user-active/<str:token>', views.CheckUserActive.as_view(), name="check-user-active"),
    path('get-refferals', views.ReferralList.as_view(), name="refferal users"),
    path('get-user-code', views.UserCodeAPIView.as_view(), name="userCode"),
    path('password-reset', views.ForgotPasswordView.as_view()),
    path('password-reset-pin-verify', views.CheckForgotPasswordPin.as_view()),
    path('reset-password-complete', views.UserResetPasswordView.as_view(), name="password-forget-complete")

   ]
