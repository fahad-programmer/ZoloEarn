from django.urls import path
from . import views


urlpatterns = [
    path("spin-wheel", views.SpinWheelView.as_view()),
    path('daily-check-in', views.DailyCheckIn.as_view()),
    path("wallet", views.WalletView.as_view(), name="wallet-view")
]
