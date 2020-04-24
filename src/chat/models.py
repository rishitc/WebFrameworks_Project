from django.db import models
from django.contrib.auth import get_user_model

from django.conf import settings

from django.db.models import Q


class ThreadManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def by_user(self, user):
        # qlookup = Q(first=user) | Q(second=user)
        # qlookup2 = Q(first=user) & Q(second=user)

        # either you are first and you can see the thread or you are second
        # and you can see the thread
        qlookup = (Q(first=user) & Q(visible_for_first=True)) |\
                  (Q(second=user) & Q(visible_for_second=True))
        # A single user cannot be the user and other_user
        # at the same time
        qlookup2 = Q(first=user) & Q(second=user)
        qs = self.get_queryset().filter(qlookup).exclude(qlookup2).distinct()
        return qs

    def get_or_new(self, user, other_username):  # get_or_create
        username = user.username
        if username == other_username:
            return None
        qlookup1 = Q(first__username=username) &\
            Q(second__username=other_username)
        qlookup2 = Q(first__username=other_username) &\
            Q(second__username=username)
        qs = self.get_queryset().filter(qlookup1 | qlookup2).distinct()
        if qs.count() == 1:
            return qs.first(), False
        elif qs.count() > 1:
            return qs.order_by('timestamp').first(), False
        else:
            User_Model_Class = user.__class__
            user2 = User_Model_Class.objects.get(username=other_username)
            if user != user2:
                obj = self.model(
                        first=user,
                        second=user2
                    )
                obj.save()
                return obj, True
            return None, False

    def hide_thread_for_user(self, user, other_user):
        user_id = get_user_model().objects.get(username=user).id
        other_user_id = get_user_model().objects.get(username=other_user).id
        # The user can be the first
        # The other_user can be the second
        query1 = Q(first=user_id) & Q(second=other_user_id)

        # The other_user  can be the first
        # The user can be the second
        query2 = Q(first=other_user_id) & Q(second=user_id)

        # If the user is first, it must be visible to them
        # initially or if the user is second then also it
        # must be visible to them initially
        query3 = (Q(first=user_id) & Q(visible_for_first=True)) |\
                 (Q(second=user_id) & Q(visible_for_second=True))

        final_query = (query1 | query2) & query3
        thread_to_hide = self.get_queryset().filter(final_query)

        # If the result of the query is not empty
        if thread_to_hide:
            # Taking the first element of the queryset
            # returned and using it
            thread_to_hide = thread_to_hide[0]
            if(thread_to_hide.first == user):
                thread_to_hide.visible_for_first = False
            else:
                thread_to_hide.visible_for_second = False
            
            thread_to_hide.save()
            # returing true to indicate successful
            # identification and removal
            return True
        # returing false to indicate no action
        # was taken
        return False

    # gets the list of users, the user has spoken to before from the DB
    def getUserChatList(self, username):
        # Get the id of the user in the user table
        user_id = get_user_model().objects.get(username=username).id

        contactList = []

        # Search for the threads the user is part of
        thread_list = self.by_user(user_id)

        # Get a list of the other participating usernames, if the threadList
        # is not empty
        if thread_list:
            for i in thread_list:
                user_first = i.first.username
                user_second = i.second.username
                latest_message = i.getLatestMessage()

                if user_first == username:
                    contactList.append({"other_user": user_second,
                                        "latest_message": latest_message})
                else:
                    contactList.append({"other_user": user_first,
                                        "latest_message": latest_message})

        return contactList


class Thread(models.Model):
    first = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              related_name='chat_thread_first')
    second = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE,
                               related_name='chat_thread_second')

    # The boolean values indicate
    # True -> The thread is visible for the user
    # False -> The thread is not visible for the user
    visible_for_first = models.BooleanField(default=True)
    visible_for_second = models.BooleanField(default=True)

    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = ThreadManager()

    @property
    def room_group_name(self):
        return f'chat_{self.id}'

    def broadcast(self, msg=None):
        if msg is not None:
            broadcast_msg_to_chat(msg, group_name=self.room_group_name, user='admin')
            return True
        return False

    def getLatestMessage(self):
        latest_chat_message = self.chatmessage_set.order_by("-timestamp")
        if latest_chat_message:
            latest_chat_message = latest_chat_message[0]
            latest_chat_message = {"user": latest_chat_message.user.username,
                                   "message": latest_chat_message.message,
                                   "timestamp": latest_chat_message.timestamp}
        else:
            latest_chat_message = {
                                   "user": "ChitChat Bot",
                                   "message": "Click here to begin chatting...",
                                   "timestamp": "This thread was created on " +
                                   self.timestamp.
                                   strftime("%B %d, %Y, %I:%M %p")
                                   }
        return latest_chat_message

    def __str__(self):
        latest_chat_message = self.chatmessage_set.order_by("-timestamp")
        if latest_chat_message:
            latest_chat_message = latest_chat_message[0]
            return " ".join([latest_chat_message.user.username,
                            " - ", latest_chat_message.message])
        else:
            return "No chatting has begun"


class ChatMessage(models.Model):
    thread = models.ForeignKey(Thread, null=True, blank=True,
                               on_delete=models.SET_NULL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='sender',
                             on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to="user_profile_images/%Y/%m/%d/",
                                      height_field="profile_image_height",
                                      width_field="profile_image_width",
                                      max_length=100,
                                      null=True,
                                      blank=True
                                      )

    profile_image_height = models.BigIntegerField(null=True,
                                                  blank=True,
                                                  default=200
                                                  )
    profile_image_width = models.BigIntegerField(null=True,
                                                 blank=True,
                                                 default=200
                                                 )


class LiveChatRoomLogger(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def getChatRoomName(self, user, other_user):
        query1 = Q(user=user)
        query2 = Q(user=other_user)

        part_a = self.get_queryset().filter(query1)
        part_b = self.get_queryset().filter(query2)
        answerSet = [i.chat_room_name for i in part_a]

        for i in part_b:
            if(i.chat_room_name in answerSet):
                return i.chat_room_name

    def showLiveChatRooms(self):
        result = self.get_queryset().all()
        print("The open chat rooms are:")
        if not result:
            print("No rooms are currently online.")
        else:
            for i in result:
                print(f"user: {i.user}")
                print(f"Socket Channel Name: {i.sockets_channel_name}")
                print(f"Chat Room Name: {i.chat_room_name}")
                print(f"Created On: {i.time_of_creation}")
                print("-"*20)

    def deleteChannel(self, user, sockets_channel_name):
        try:
            self.get_queryset().get(sockets_channel_name=sockets_channel_name,
                                    user=user)\
                .delete()
        except CurrentChatRooms.DoesNotExist:
            print("f{sockets_channel_name} does not exist!")

    def add_new_Channel(self, user, sockets_channel_name, chat_room_name):
        obj = CurrentChatRooms(user=user,
                               sockets_channel_name=sockets_channel_name,
                               chat_room_name=chat_room_name)
        obj.save()
        # print("Insertion with the below entires has taken place:")
        # print(f"user: {user}")
        # print(f"sockets_channel_name: {sockets_channel_name}")
        # print(f"chat_room_name: {chat_room_name}")
        # print(f"time_of_creation: {obj.time_of_creation}")
        # print("-"*20)

    # Every time the server is started we need to clear the
    # contents of the CurrentChatRooms model, so we write the
    # required function here
    def clear_logs(self):
        self.get_queryset().all().delete()


# Store the current open chat rooms
class CurrentChatRooms(models.Model):
    sockets_channel_name = models.TextField()
    user = models.CharField(max_length=151)
    chat_room_name = models.TextField()
    time_of_creation = models.DateTimeField(auto_now_add=True)

    objects = LiveChatRoomLogger()

    def __str__(self):
        return (f"user: {self.user} : " +
                f"sockets_channel_name: {self.sockets_channel_name} : " +
                f"chat_room_name: {self.chat_room_name} : " +
                f"time_of_creation: {self.time_of_creation}")
