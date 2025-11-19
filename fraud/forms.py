from django import forms

# Help text for phone field
PHONE_HELP = "Use international format (e.g., +911234567890)"

# Transaction categories
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


# ---------------------- Register Form ----------------------
class RegisterForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Choose a username"}),
        label="Username"
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": "your@email.com"}),
        label="Email"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Enter password"}),
        label="Password"
    )
    phone_number = forms.CharField(
        max_length=20,
        help_text=PHONE_HELP,
        widget=forms.TextInput(attrs={"placeholder": "+91XXXXXXXXXX"}),
        label="Phone number"
    )


# ---------------------- Transaction Form ----------------------
class TransactionForm(forms.Form):
    phone_number = forms.CharField(
        label="Phone number",
        max_length=20,
        help_text=PHONE_HELP,
        widget=forms.TextInput(attrs={"placeholder": "+91XXXXXXXXXX"})
    )

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        label="Category"
    )

    amt = forms.DecimalField(
        label="Amount",
        max_digits=12,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={"step": "0.01", "placeholder": "Enter amount"})
    )

    city = forms.CharField(
        max_length=100,
        label="City",
        widget=forms.TextInput(attrs={"placeholder": "e.g., New Delhi"})
    )

    # New fields replacing state, job, and age
    card_number = forms.CharField(
        max_length=16,
        label="Card Number",
        widget=forms.TextInput(attrs={
            "placeholder": "XXXX XXXX XXXX 1234",
            "pattern": r"\d{16}",
            "inputmode": "numeric"
        }),
        help_text="Enter a valid 16-digit card number"
    )

    cvv = forms.CharField(
        max_length=4,
        label="CVV",
        widget=forms.PasswordInput(attrs={
            "placeholder": "•••",
            "inputmode": "numeric",
            "maxlength": "4"
        }),
        help_text="3 or 4 digit code on back of card"
    )

    expiry_date = forms.CharField(
        max_length=7,
        label="Expiry Date (MM/YYYY)",
        widget=forms.TextInput(attrs={"placeholder": "MM/YYYY"}),
        help_text="Enter card expiry in MM/YYYY format"
    )

    # Hour as time input (HTML <input type="time">)
    hour_time = forms.TimeField(
        label="Hour (time)",
        widget=forms.TimeInput(attrs={"type": "time"}),
        help_text="Pick a time (we’ll use the hour 0–23)"
    )

    # Day of week (new addition)
    dow = forms.IntegerField(
        min_value=0,
        max_value=6,
        label="Day of Week (0=Mon, 6=Sun)",
        widget=forms.NumberInput(attrs={"placeholder": "0–6"})
    )


# ---------------------- OTP Form ----------------------
class OTPForm(forms.Form):
    otp_code = forms.RegexField(
        regex=r"^\d{6}$",
        label="Enter 6-digit OTP",
        max_length=6,
        min_length=6,
        error_messages={"invalid": "Please enter a 6-digit numeric code."},
        widget=forms.TextInput(attrs={
            "placeholder": "••••••",
            "inputmode": "numeric"
        })
    )
