from django.urls import path
from . import views


urlpatterns = [
    path("spin-wheel", views.SpinWheelView.as_view())
]
