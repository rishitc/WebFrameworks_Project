from django.urls import path, re_path

from .views import ThreadView, InboxView, LoadProfileView, searchUser,\
                   loginUser, signupUser, homePage, logoutUser, edit_profile,\
                   change_password, leaveThreadHandler

app_name = 'chat'
urlpatterns = [
    path("", InboxView.as_view()),
    re_path(r"^chatbox/(?P<username>[\w.@+-]+)/$", ThreadView.as_view(),
            name="chatBox"),
    re_path(r"^search/username/$", searchUser, name="searchUser"),
    re_path(r"^login/$", loginUser, name="login"),
    re_path(r"^logout/$", logoutUser, name="logout"),
    re_path(r"^signup/$", signupUser, name="signup"),
    re_path(r"^home/$", homePage, name="home"),
    re_path(r"^profile/edit/$", edit_profile, name="edit_profile"),
    re_path(r"^profile/password/$", change_password,
            name="change_password"),
    path("profile/", LoadProfileView.as_view(), name="profile"),
    path("threads/leave-thread/", leaveThreadHandler, name="leave_thread"),
    # re_path(r'^reset-password/$', password_reset, name='reset_password'),
    # re_path(r'^reset-password/done/$', password_reset_done,
    #         name='password_reset_done'),
    # re_path(r'^reset-password/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$',
    #         password_reset_confirm, name='password_reset_confirm'),
    # re_path(r'^reset-password/complete/$',
    #         password_reset_complete, name='password_reset_complete'),
]
