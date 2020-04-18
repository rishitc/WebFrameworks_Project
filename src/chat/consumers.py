import asyncio
import json
from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async

from .models import Thread, ChatMessage


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
        await self.channel_layer.group_add(
            chat_room,
            self.channel_name
        )
        await self.send({
            "type": 'websocket.accept'
        })

    async def websocket_receive(self, event):
        # When a message is received from the websocket
        print("receive", event)
        front_text = event.get("text", None)
        if front_text is not None:
            loaded_dict_data = json.loads(front_text)
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

    @database_sync_to_async
    def get_thread(self, user, other_user):
        return Thread.objects.get_or_new(user, other_user)[0]

    @database_sync_to_async
    def create_chat_message(self, message):
        thread_obj = self.thread_obj
        user = self.me
        return ChatMessage.objects.create(thread=thread_obj, user=user,
                                          message=message)
