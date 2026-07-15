from django.db import models
from appointments.models import Appointment


class Bill(models.Model):

    PAYMENT_STATUS = [
        ("Pending", "Pending"),
        ("Paid", "Paid"),
        ("Cancelled", "Cancelled"),
    ]

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="bill"
    )

    consultation_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    medicine_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    lab_test_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    gst = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="Pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):

        self.total_amount = (
            self.consultation_fee +
            self.medicine_cost +
            self.lab_test_cost +
            self.gst -
            self.discount
        )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Bill #{self.id}"
    @property
    def total_paid(self):
        return sum(p.amount_paid for p in self.payments.all())

    @property
    def balance_due(self):
        return self.total_amount - self.total_paid
class Payment(models.Model):

    PAYMENT_MODE = [
        ("Cash", "Cash"),
        ("Card", "Card"),
        ("UPI", "UPI"),
        ("Insurance", "Insurance"),
    ]

    bill = models.ForeignKey(
        Bill,
        on_delete=models.CASCADE,
        related_name="payments"
    )

    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_mode = models.CharField(
        max_length=20,
        choices=PAYMENT_MODE
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="UPI ref no. / card last 4 digits / cheque no. etc."
    )

    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.bill} - ₹{self.amount_paid}"