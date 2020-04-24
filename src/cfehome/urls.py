"""cfehome URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

from django.contrib.auth.views import PasswordResetView,\
                                      PasswordResetDoneView,\
                                      PasswordResetConfirmView,\
                                      PasswordResetCompleteView

from chat.models import CurrentChatRooms

urlpatterns = [
    path('', TemplateView.as_view(template_name="home.html")),
    path('admin/', admin.site.urls),
    path('chitchat/', include('chat.urls')),
    re_path(r'^emoji/', include('emoji.urls')),
    # Enter your email and request a password reset here
    path('profile/password-reset/',
         PasswordResetView.as_view(
          template_name="chat/password_reset.html",
          extra_context={"page_name": "Reset Password"}
          ),
         name="password_reset",
         ),

    # Sends the email
    path('profile/password-reset/done/',
         PasswordResetDoneView.as_view(
          template_name="chat/password_reset_done.html",
          extra_context={"page_name": "Link Sent"}
          ),
         name="password_reset_done"
         ),

    # Takes you to the password reset form
    path('profile/password-reset-confirm/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(
          template_name="chat/password_reset_confirm.html",
          extra_context={"page_name": "Password Reset Form"}
          ),
         name="password_reset_confirm"
         ),

    # Final view to complete the password reset process
    path('profile/password-reset-complete/',
         PasswordResetCompleteView.as_view(
          template_name="chat/password_reset_complete.html",
          extra_context={"page_name": "Password Reset Complete"}
          ),
         name="password_reset_complete",
         ),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)


# Every time the server is started we need to clear the
# contents of the CurrentChatRooms model, so we do that here
CurrentChatRooms.objects.clear_logs()
