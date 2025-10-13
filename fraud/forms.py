# fraud/forms.py
from django import forms

PHONE_HELP = "Use international format (e.g., +911234567890)"

CATEGORY_CHOICES = [
    ("grocery_pos", "Grocery (POS)"),
    ("misc_pos", "Misc POS"),
    ("shopping_pos", "Shopping (POS)"),
    ("shopping_net", "Shopping (Online)"),
    ("gas_transport", "Gas/Transport"),
    ("entertainment", "Entertainment"),
    ("food_dining", "Food & Dining"),
    ("health_fitness", "Health & Fitness"),
    ("travel", "Travel"),
    ("misc_net", "Misc Online"),
]
class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    phone_number = forms.CharField(max_length=20, help_text=PHONE_HELP)
    
class TransactionForm(forms.Form):
    phone_number = forms.CharField(
        label="Phone number",
        max_length=20,
        help_text=PHONE_HELP,
        widget=forms.TextInput(attrs={"placeholder": "+91XXXXXXXXXX"})
    )
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, label="Category")
    amt = forms.DecimalField(
        label="Amount",
        max_digits=12,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={"step": "0.01"})
    )
    city = forms.CharField(max_length=100, label="City")
    state = forms.CharField(max_length=50, label="State")
    job = forms.CharField(max_length=100, label="Job")

    # Hour as time input (HTML <input type="time">)
    hour_time = forms.TimeField(
        label="Hour (time)",
        widget=forms.TimeInput(attrs={"type": "time"}),
        help_text="Pick a time (we’ll use the hour 0–23)"
    )

    age = forms.IntegerField(min_value=0, max_value=120, label="Age")

class OTPForm(forms.Form):
    otp_code = forms.RegexField(
        regex=r"^\d{6}$",
        label="Enter 6-digit OTP",
        max_length=6,
        min_length=6,
        error_messages={"invalid": "Please enter a 6-digit numeric code."},
        widget=forms.TextInput(attrs={"placeholder": "••••••", "inputmode": "numeric"})
    )
