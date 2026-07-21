from django.db import models
from billing.models import Bill


class Payment(models.Model):

    PAYMENT_METHOD_CHOICES=[
        ("Cash","Cash"),
        ("UPI","UPI"),
        ("Card","Card"),
        ("Net Banking","Net Banking"),
    ]

    PAYMENT_STATUS_CHOICES=[
        ("Pending","Pending"),
        ("Success","Success"),
        ("Failed","Failed"),
        ("Refunded","Refunded"),
    ]

    bill=models.OneToOneField(
        Bill,
        on_delete=models.CASCADE,
        related_name="payment"
    )

    payment_method=models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )

    transaction_id=models.CharField(
        max_length=100,
        unique=True
    )

    amount=models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_status=models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="Pending"
    )

    payment_date=models.DateTimeField(
        auto_now_add=True
    )

    remarks=models.TextField(
        blank=True,
        null=True
    )

    received_by=models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Cashier or Admin Name"
    )

    receipt_number=models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True
    )

    created_at=models.DateTimeField(
        auto_now_add=True
    )

    updated_at=models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering=["-payment_date"]

    def __str__(self):
        return f"{self.transaction_id} - {self.bill.patient.user.get_full_name()}"