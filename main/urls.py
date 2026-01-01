from django.urls import path

from main.views.web import login

urlpatterns = [
    path('<str:org_code>/login/', login, name='login'),
    path('<str:org_code>/dashboard/', login, name='dashboard'),
]