from django.db import models
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user.username}: {self.content[:30]}"
class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    video = models.FileField(upload_to='posts/videos/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username}'s Post"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user.username} Comment"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)

    bio = models.TextField(blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', default='default_profile.png')
    created_at = models.DateTimeField(auto_now_add=True)

    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.full_name

    # ✅ Correct position — inside Profile class
    def is_user_online(self):
        from django.utils import timezone
        if self.last_seen:
            now = timezone.now()
            return (now - self.last_seen).seconds < 60  # < 1 minute
        return False
class PrivateMessage(models.Model):
    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_messages", on_delete=models.CASCADE)
    
    content = models.TextField(blank=True)  # text message
    file = models.FileField(upload_to="private_chat/", blank=True, null=True)  # file upload
    file_url = models.URLField(blank=True, null=True)  # URL for WebSocket
    
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

class ChatGroup(models.Model):
    name=models.CharField(max_length=255)
    image=models.ImageField(upload_to="group_pics/", blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_groups")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
class GroupMember(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)

    class Meta:
        unique_together = ("group", "user")

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"


class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    file = models.FileField(upload_to="group_files/", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} → {self.group.name}"
