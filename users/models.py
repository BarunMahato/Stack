from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        LIBRARIAN = 'LIBRARIAN', 'Librarian'
        MEMBER = 'MEMBER', 'Member'

    name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)
    total_credits_spent = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    @property
    def total_credits_earned(self) -> Decimal:
        elapsed_seconds = max(0.0, (timezone.now() - self.created_at).total_seconds())
        completed_days = int(elapsed_seconds // 86400)
        return Decimal(5 + (completed_days * 5))

    @property
    def available_credits(self) -> Decimal:
        return self.total_credits_earned - self.total_credits_spent