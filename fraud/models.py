from django.db import models

# Create your models here.
# fraud/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone_number = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ({self.phone_number})"

class Transaction(models.Model):
    DECISION_CHOICES = [
        ("allowed", "Allowed"),
        ("challenge", "Challenged (OTP sent)"),
        ("approved", "Approved after OTP"),
        ("blocked", "Blocked / OTP failed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="txns")

    # inputs you now collect
    category = models.CharField(max_length=64)
    amt = models.DecimalField(max_digits=12, decimal_places=2)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    job = models.CharField(max_length=100)
    hour = models.PositiveSmallIntegerField()
    dow = models.PositiveSmallIntegerField()
    age = models.PositiveSmallIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    # model + rule diagnostics
    ml_prob = models.FloatField(null=True, blank=True)
    rule_avg_last_n = models.FloatField(null=True, blank=True)
    rule_multiplier_used = models.FloatField(null=True, blank=True)
    rule_delta_used = models.FloatField(null=True, blank=True)
    rule_flag = models.BooleanField(default=False)

    # OTP tracking
    otp_required = models.BooleanField(default=False)
    otp_id = models.CharField(max_length=64, null=True, blank=True)
    otp_verified = models.BooleanField(default=False)

    final_decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default="allowed")
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Txn#{self.id} {self.user.username} {self.amt} {self.category} [{self.final_decision}]"
