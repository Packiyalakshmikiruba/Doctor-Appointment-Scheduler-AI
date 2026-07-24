from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Message(models.Model):

    MESSAGE_TYPE_CHOICES = [
        ("TEXT", "Text"),
        ("IMAGE", "Image"),
        ("FILE", "File"),
        ("VOICE", "Voice Note"),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    body = models.TextField(blank=True)

    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default="TEXT")
    attachment = models.FileField(upload_to="chat_attachments/%Y/%m/", blank=True, null=True)

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.message_type}"