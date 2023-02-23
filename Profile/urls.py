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
    path('referral', views.ReferralView.as_view())

   ]
