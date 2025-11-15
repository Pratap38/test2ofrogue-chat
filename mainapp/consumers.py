import json
import os
import uuid
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings

# ------------------------ GLOBAL CHAT ------------------------
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs'].get('room_name', None)
        self.room_group_name = f"chat_{self.room_name}" if self.room_name else "global_chat"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        data = json.loads(text_data)
        username = data.get("username", "Anonymous")
        message = data.get("message", "")

        if not message.strip():
            return

        if not self.room_name:
            await self.save_global_message(username, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "chat_message", "username": username, "message": message},
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "username": event["username"],
            "message": event["message"],
        }))

    @database_sync_to_async
    def save_global_message(self, username, message):
        from django.contrib.auth import get_user_model
        from .models import Message

        User = get_user_model()
        user, _ = User.objects.get_or_create(username=username)
        Message.objects.create(user=user, content=message)


# ------------------------ PRIVATE CHAT ------------------------
class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"private_{self.room_name}"

        # Assign a temporary username for anonymous users
        if self.scope["user"].is_anonymous:
            # Create a guest username
            import random, string
            guest_name = "Guest_" + "".join(random.choices(string.ascii_letters + string.digits, k=6))
            self.scope["user"].username = guest_name

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

 async def receive(self, text_data=None):
    if not text_data:
        return
    data = json.loads(text_data)

    # Typing indicator
    if data.get("type") == "typing":
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_status",
                "username": self.scope["user"].username,
                "typing": data.get("typing", False),
            }
        )
        return

    # For private messages
    sender = self.scope["user"].username
    receiver = data.get("receiver")
    message = data.get("message", "")
    file_url = data.get("file_url")

    await self.save_message(sender, receiver, message, file_url)

    await self.channel_layer.group_send(
        self.room_group_name,
        {
            "type": "private_message",
            "sender": sender,
            "receiver": receiver,
            "message": message,
            "file_url": file_url,
        }
    )


    async def private_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def typing_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "typing",
            "username": event["username"],
            "typing": event["typing"]
        }))

  @database_sync_to_async
def save_message(self, sender, receiver, message, file_url=None):
    from django.contrib.auth import get_user_model
    from .models import PrivateMessage

    User = get_user_model()
    try:
        sender_user = User.objects.get(username=sender)
    except User.DoesNotExist:
        sender_user = User.objects.create(username=sender)

    try:
        receiver_user = User.objects.get(username=receiver)
    except User.DoesNotExist:
        receiver_user = User.objects.create(username=receiver)

    PrivateMessage.objects.create(
        sender=sender_user,
        receiver=receiver_user,
        content=message or "",
        file=file_url or None
    )

    @database_sync_to_async
    def save_file(self, file_base64):
        header, data = file_base64.split(";base64,")
        ext = header.split("/")[-1] or "bin"
        filename = f"{uuid.uuid4()}.{ext}"
        rel_path = os.path.join("private_files", filename)
        abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(base64.b64decode(data))

        return settings.MEDIA_URL + rel_path


# ------------------------ GROUP CHAT ------------------------
class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.group_name = f"group_{self.group_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None):
        data = json.loads(text_data)
        sender = data.get("sender")
        message = data.get("message", "")
        file_data = data.get("file")

        file_url = None
        if file_data:
            file_url = await self.save_file(file_data)

        await self.save_message(sender, message, file_url)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "group_message",
                "sender": sender,
                "message": message,
                "file_url": file_url,
            }
        )

    async def group_message(self, event):
        await self.send(text_data=json.dumps({
            "sender": event["sender"],
            "message": event["message"],
            "file_url": event.get("file_url")
        }))

    @database_sync_to_async
    def save_message(self, sender, message, file_url):
        from django.contrib.auth import get_user_model
        from .models import ChatGroup, GroupMessage

        User = get_user_model()
        sender_user = User.objects.get(username=sender)
        group = ChatGroup.objects.get(id=self.group_id)

        GroupMessage.objects.create(
            group=group,
            sender=sender_user,
            content=message,
            file=file_url
        )

    @database_sync_to_async
    def save_file(self, file_base64):
        header, data = file_base64.split(";base64,")
        ext = header.split("/")[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        file_path = os.path.join("group_files", filename)
        abs_path = os.path.join(settings.MEDIA_ROOT, file_path)

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

        with open(abs_path, "wb") as f:
            f.write(base64.b64decode(data))

        return f"{settings.MEDIA_URL}{file_path}"
