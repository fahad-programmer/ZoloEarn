from django.urls import path
from . import views

urlpatterns = [
    path("spin-wheel", views.SpinWheelView.as_view()),
    path('daily-check-in', views.DailyCheckIn.as_view()),
    path("wallet", views.WalletView.as_view(), name="wallet-view"),
    path('get-user-spin-turn', views.UserSpinTurn.as_view()),
    path('add-user-spin-turn', views.UserSpinFree.as_view()),
    path("get-user-ttc-turns", views.userTTCAvailabeTurn.as_view()),
    path("add-ttc-turn", views.addUserTTCTurn.as_view()),
    path('ttc-turn', views.TTCApiView.as_view()),
    path('ttc-user-lose', views.TTCLoseApi.as_view()),
    path('monster-hunter-turns', views.MonsterHunterTurn.as_view()),
    path('add-monster-hunter', views.AddMonsterHunterApi.as_view()),
    path('monster-hunter', views.MonsterHunterApi.as_view({'post': 'post'})),
    path('quiz', views.QuizInQuestions.as_view({'post': 'post'})),
    path('quizApi', views.QuizApi.as_view({'post': 'post'})),
    path('addQuizApi', views.AddQuizInApi.as_view()),
    path('quizTurns', views.QuizInTurns.as_view()),
    path("automatequiz", views.load_questions_from_json_view, name="nothing"),
    path("getZoloVideos", views.GetZoloVideos.as_view()),
    path("ZoloVideoApi", views.ZoloVideoApi.as_view())
]




