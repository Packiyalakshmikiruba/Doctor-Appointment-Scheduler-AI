from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class SupportMessage(models.Model):
    """Real human-to-human messages between a patient and admin/support staff."""

    patient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="support_messages_sent"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="support_messages_authored"
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.username}: {self.message[:40]}"