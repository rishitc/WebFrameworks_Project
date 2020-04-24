from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic.edit import FormMixin
from django.views.generic.base import ContextMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm,\
                                      PasswordChangeForm
from django.contrib.auth import login, logout,\
                                update_session_auth_hash
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.db.models import Q
import json
from urllib.parse import urlencode
from django.views.generic import DetailView, ListView

from .forms import ComposeForm, UserSearchForm, UserProfileImageForm,\
                   RegistrationForm, EditUserProfileForm

from .models import Thread, ChatMessage, CurrentChatRooms


class InboxView(LoginRequiredMixin, ListView):
    template_name = 'chat/inbox.html'

    def get_queryset(self):
        return Thread.objects.by_user(self.request.user)


class ThreadView(LoginRequiredMixin, FormMixin, DetailView):
    template_name = 'chat/thread.html'
    form_class = ComposeForm
    success_url = './'
    model = Thread

    def get_queryset(self):
        obj = Thread.objects.by_user(self.request.user)
        if obj is None:
            raise Http404
        return obj

    def get_object(self):
        other_username = self.kwargs.get("username")
        obj, created = Thread.objects.get_or_new(self.request.user,
                                                 other_username)
        if obj is None:
            raise Http404
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        context['page_name'] = 'ChitChat'
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        thread = self.get_object()
        user = self.request.user
        message = form.cleaned_data.get("message")
        ChatMessage.objects.create(user=user, thread=thread, message=message)
        return super().form_valid(form)


class LoadProfileView(LoginRequiredMixin, FormMixin, DetailView, ContextMixin):
    template_name = 'chat/profile.html'
    form_class = UserSearchForm
    success_url = './'
    model = get_user_model()

    # returns a dictionary containing the users the user has
    # chatted with before
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        userChatList = Thread.objects.\
            getUserChatList(self.request.user.username)
        userChatList = self.pack_2_tuple(userChatList)
        context['userChatList'] = userChatList
        context['page_name'] = "User Profile"
        return context

    def pack_2_tuple(self, _list):
        new_list = list(zip(_list[::2], _list[1::2]))
        if len(_list) % 2:
            new_list.append((_list[-1], None))
        return new_list

    def get_object(self):
        username = self.request.user.username
        if self.request.user.is_authenticated:
            obj = get_user_model().objects.get(username=username)
            if obj is None:
                raise Http404
            return obj
        else:
            raise Http404

@login_required()
def searchUser(request):
    if request.user.is_authenticated and request.method == 'POST' and\
       request.is_ajax():
        # I want a list of users that match the searchString but they must not be
        # the requesting user itself
        userMatchingQuery_part1 = Q(username__contains=request.POST.
                                    get("searchString"))
        userMatchingQuery_part2 = ~Q(username__contains=request.user.username)

        # Get the top 10 matching queries
        matchedUsers = get_user_model().objects.\
            filter(userMatchingQuery_part1, userMatchingQuery_part2)[:10]
        print(request.POST.get("searchString"))
        matchedUsers_username = []
        for i in matchedUsers:
            matchedUsers_username.append(i.username)
        matchedUsers_username = json.dumps({"userList": matchedUsers_username})
        return HttpResponse(matchedUsers_username,
                            content_type="application/json")
    else:
        raise HttpResponseForbidden('403 Forbidden. Access Denied',
                                    content_type='text/html')


def loginUser(request):
    if request.user.is_authenticated:
        # get the redirection url ready
        # /profile/
        base_url = reverse('chat:profile')
        # completing the redirection url ready
        query_string = urlencode({'status': "user_already_logged_in"})

        # /profile/?status=Success
        url = '{}?{}'.format(base_url, query_string)
        return redirect(url)

    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)

        # get the redirection url ready
        # /profile/
        base_url = reverse('chat:profile')

        # if user details are valid
        if form.is_valid():
            # login the user
            user = form.get_user()
            login(request, user)
            # ---------------
            if(request.GET.get('next') is not None):
                return redirect(request.GET.get('next'))
            else:
                # completing the redirection url ready
                query_string = urlencode({'status': 'success_user_login'})

                # /profile/?status=Success
                url = '{}?{}'.format(base_url, query_string)
                return redirect(url)
    else:
        form = AuthenticationForm()

    return render(request, "chat/login.html", {
                                               'form': form,
                                               'page_name': 'Login'
                                              })


def signupUser(request):
    if request.user.is_authenticated:
        # get the redirection url ready
        # /profile/
        base_url = reverse('chat:profile')
        # completing the redirection url ready
        query_string = urlencode({'status': "user_already_logged_in"})

        # /profile/?status=user_already_logged_in
        url = '{}?{}'.format(base_url, query_string)
        return redirect(url)

    if request.method == "POST":
        UserForm = RegistrationForm(request.POST)
        UserProfileImage = UserProfileImageForm(request.FILES)
        # if user details are valid
        if UserForm.is_valid() and UserProfileImage.is_valid():
            user = UserForm.save()

            if request.FILES:
                # setting the user filed for the form so that
                # it save correctly
                UserProfileImage.user = user
                UserProfileImage.save()
            # login the user
            login(request, user)
            # ---------------
        if(request.GET.get('next') is not None):
            return redirect(request.GET.get('next'))
        else:
            # get the redirection url ready
            # /profile/
            base_url = reverse('chat:profile')
            # completing the redirection url ready
            query_string = urlencode({'status': "success_user_register"})

            # /profile/?status=success_user_register
            url = '{}?{}'.format(base_url, query_string)
            return redirect(url)
    else:
        UserForm = RegistrationForm()
        ImageForm = UserProfileImageForm()

    return render(request, "chat/signup.html", {'UserForm': UserForm,
                  'ImageForm': ImageForm, 'page_name': 'Signup'})


def homePage(request):
    return render(request, "home.html", {'page_name': 'Home'})


def logoutUser(request):
    if request.method == 'POST':
        # If the user is logged in
        if request.user.is_authenticated:
            logout(request)
            return redirect('chat:home')
        # If the user is not logged in
        else:
            return redirect('chat:home')
    # If this is not a POST request
    else:
        return redirect('chat:login')


@login_required()
def edit_profile(request):
    # userProfileImage_query = get_user_model().objects.get(pk=request.user.id).\
    #                    userprofile

    if request.method == "POST":
        user_form = EditUserProfileForm(request.POST, instance=request.user)
        UserProfileImage = UserProfileImageForm(request.FILES, instance=request.user.userprofile)
        # print(UserForm.data)
        # userProfileImage_form = UserProfileImageForm(
        #     instance=userProfileImage_query)

        if user_form.is_valid():
            obj = user_form.save()

            if request.FILES:
                # setting the user filed for the form so that
                # it save correctly
                UserProfileImage.user = obj
                UserProfileImage.save()

            # get the redirection url ready
            # /profile/
            base_url = reverse('chat:profile')
            # completing the redirection url ready
            query_string = urlencode({'status': 'success_det_chg'})

            # /profile/?status=success_det_chg
            url = '{}?{}'.format(base_url, query_string)
            return redirect(url)
            # UserForm.save()
            # # setting the user filed for the form so that
            # # it save correctly
            # userProfileImage_form.user = request.user

            # if request.FILES:
            #     userProfileImage_form.save()
        else:
            # get the redirection url ready
            # /edit/
            base_url = reverse('chat:edit_profile')
            # completing the redirection url ready
            query_string = urlencode({'status': 'failure_det_chg'})

            # /profile/?status=success_det_chg
            url = '{}?{}'.format(base_url, query_string)
            return redirect(url)

    else:
        user_form = EditUserProfileForm(instance=request.user)
        ImageForm = UserProfileImageForm(instance=request.user.userprofile)
        return render(request, "chat/edit_profile.html",
                      {
                          'EditForm': user_form,
                          'ImageForm': ImageForm,
                          'page_name': 'Edit Profile'
                      })

    return redirect('chat:profile')


@login_required()
def change_password(request):
    if request.method == 'POST':
        pwd_form = PasswordChangeForm(data=request.POST, user=request.user)

        # get the redirection url ready
        # /profile/
        base_url = reverse('chat:profile')
        if pwd_form.is_valid():
            pwd_form.save()
            # prevent being logged out when the
            # password changes
            update_session_auth_hash(request, pwd_form.user)

            # completing the redirection url ready
            query_string = urlencode({'status': 'success_pwd_chg'})

            # /profile/?status=success_pwd_chg
            url = '{}?{}'.format(base_url, query_string)
            return redirect(url)
        else:
            # completing the redirection url ready
            query_string = urlencode({'status': 'failure_pwd_chg'})

            # /profile/?status=failure_pwd_chg
            url = '{}?{}'.format(base_url, query_string)
            return redirect(url)

    else:
        pwd_form = PasswordChangeForm(user=request.user)
        return render(request, "chat/change_pwd.html",
                      {
                          'PWD_Form': pwd_form,
                          'page_name': 'Change Password',
                          "btnName_edit": 'Edit Password',
                          "btnName_email": "Reset Password Through Email"
                      })

    return redirect('chat:profile')


# This will get 3 parameters from the
# front end using AJAX, they are:
# user
# other_user
# This will remove the visibility of the thread for user
# This will broadcast the message that the user has deleted the chat
# This will save this message by the ChitChat Bot in the DB
@login_required()
def leaveThreadHandler(request):
    if request.user.is_authenticated and request.method == 'POST' and\
       request.is_ajax():
        result = Thread.objects.hide_thread_for_user(
                                             user=request.POST.get("user"),
                                             other_user=request.POST.get("other_user")
                                             )
        if result is True:
            matchedUsers_username = json.dumps({"status": 200})
        else:
            matchedUsers_username = json.dumps({"status": 400})
            return HttpResponse(matchedUsers_username,
                                content_type="application/json")

        user = request.POST.get("user")
        broadcastMessage = f"{user} has deleted the chat."

        chat_room_name = CurrentChatRooms.objects.\
            getChatRoomName(user=request.POST.get("user"),
                            other_user=request.POST.get("other_user"))

        if not chat_room_name:
            matchedUsers_username = json.dumps({"status": 400})
            return HttpResponse(matchedUsers_username,
                                content_type="application/json")

        channel_layer = get_channel_layer()
        response_to_echo = {
                "message": broadcastMessage,
                "username": "ChitChat Bot"
        }
        async_to_sync(channel_layer.group_send)(chat_room_name, {
                                                                "type": "chat_message_event",
                                                                "text": json.dumps(response_to_echo)
                                                                }
                                                )

        thread = Thread.objects.get(id=int(chat_room_name.split("_")[1]))
        user = request.user
        message = broadcastMessage
        obj = ChatMessage.objects.create(user=user, thread=thread,
                                         message=message)
        obj.save()

        return HttpResponse(matchedUsers_username,
                            content_type="application/json")
    else:
        raise HttpResponseForbidden('403 Forbidden. Access Denied',
                                    content_type='text/html')
