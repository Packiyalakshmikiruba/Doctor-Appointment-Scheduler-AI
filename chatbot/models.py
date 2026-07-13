from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="chat_sessions")
    session_id = models.CharField(max_length=64, unique=True)
    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.session_id[:8]} - {self.user}"


class ChatLog(models.Model):
    SENDER_CHOICES = [("USER", "User"), ("BOT", "Bot")]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField()
    escalated = models.BooleanField(default=False, help_text="Handed off to human clinic staff")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"[{self.sender}] {self.message[:40]}"