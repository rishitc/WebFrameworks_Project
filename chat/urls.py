from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView
urlpatterns = [
    path('testimonials/<int:pk>/', views.testimonials, name='testimonials'),
    path('feedback/', views.feedback, name='feedback'),
    path("login/",LoginView.as_view(),name='login'),
    path("register/",views.registerView,name='register'),
    path("logout/",LogoutView.as_view(next_page='home'),name='logout'),
    path("home/",views.homeView,name='home'),
    path("index/",views.indexView,name='index'),
]