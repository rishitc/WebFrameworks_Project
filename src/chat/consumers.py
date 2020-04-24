import asyncio
import json
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
import asgiref
from channels.auth import get_user

from .models import Thread, ChatMessage, CurrentChatRooms


class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        # When a socket connects
        print("connected", event)

        other_user = self.scope['url_route']['kwargs']['username']
        me = self.scope['user']
        self.me = me
        print(f'{other_user} and {me}')
        thread_obj = await self.get_thread(me, other_user)
        self.thread_obj = thread_obj
        print(thread_obj.id)
        chat_room = f"thread_{thread_obj.id}"
        self.chat_room = chat_room
        # print(f"Chatroom: {chat_room}, {self.channel_name}, {type(self.channel_name)}")
        await self.channel_layer.group_add(
            chat_room,
            self.channel_name
        )
        # logging the creation of a channel
        await self.log_new_room(self.channel_name, chat_room)
        await self.send({
            "type": 'websocket.accept'
        })

    async def websocket_receive(self, event):
        # prevent random logouts
        get_user(self.scope)
        # When a message is received from the websocket
        print("receive", event)
        front_text = event.get("text", None)
        if front_text is not None:
            asyncJSONloads = asgiref.sync.sync_to_async(json.loads)
            loaded_dict_data = await asyncJSONloads(front_text)
            msg = loaded_dict_data.get('message')
            print(msg)

            user = self.scope['user']
            username = "Anonymous"
            if user.is_authenticated:
                username = user.username

            response_to_echo = {
                "message": msg,
                "username": username
            }

            await self.create_chat_message(msg)

            # broadcasts the message event to be sent
            await self.channel_layer.group_send(
                self.chat_room,
                {
                    "type": "chat_message_event",
                    "text": json.dumps(response_to_echo)
                }
            )

    async def chat_message_event(self, event):
        print("message", event)
        # sends the actual message
        await self.send({
            "type": "websocket.send",
            "text": event["text"]
        })

    async def websocket_disconnect(self, event):
        # When a socket disconnects
        print("disconnected", event)

        # removing the channel from the logs
        await self.remove_old_room_log(self.channel_name)
        raise StopConsumer()

    @database_sync_to_async
    def get_thread(self, user, other_user):
        return Thread.objects.get_or_new(user, other_user)[0]

    @database_sync_to_async
    def create_chat_message(self, message):
        thread_obj = self.thread_obj
        user = self.me
        return ChatMessage.objects.create(thread=thread_obj, user=user,
                                          message=message)

    @database_sync_to_async
    def log_new_room(self, channel_layer_name, chat_room_name):
        user = self.me
        CurrentChatRooms.objects.\
            add_new_Channel(user=user,
                            sockets_channel_name=channel_layer_name,
                            chat_room_name=chat_room_name)

    @database_sync_to_async
    def remove_old_room_log(self, channel_layer_name):
        user = self.me
        CurrentChatRooms.objects.\
            deleteChannel(user=user,
                          sockets_channel_name=channel_layer_name)
