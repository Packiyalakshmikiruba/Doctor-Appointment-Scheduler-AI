from django.contrib import admin
from .models import ChatSession, ChatLog


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "user", "started_at")


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ("session", "sender", "message", "escalated", "timestamp")
    list_filter = ("sender", "escalated")