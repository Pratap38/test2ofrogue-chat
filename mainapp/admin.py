from django.contrib import admin
from .models import Message, Post, Comment, Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'created_at')
    search_fields = ('full_name', 'email', 'phone')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'description', 'timestamp')
    search_fields = ('user__username', 'description')
    list_filter = ('timestamp',)
    ordering = ('-timestamp',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'text', 'timestamp')
    search_fields = ('user__username', 'post__description', 'text')
    list_filter = ('timestamp',)
    ordering = ('-timestamp',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'timestamp')
    search_fields = ('user__username', 'content')
    list_filter = ('timestamp',)
    ordering = ('-timestamp',)
