# fraud/views.py
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from requests import HTTPError, RequestException

from .forms import RegisterForm, TransactionForm, OTPForm
from .models import UserProfile, Transaction
from .utils import score_transaction, send_otp, verify_otp


# ------- Registration --------
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            u = form.cleaned_data["username"]
            p = form.cleaned_data["password"]
            e = form.cleaned_data.get("email") or ""
            phone = form.cleaned_data["phone_number"].strip()

            from django.contrib.auth.models import User
            if User.objects.filter(username=u).exists():
                messages.error(request, "Username already taken.")
            elif UserProfile.objects.filter(phone_number=phone).exists():
                messages.error(request, "Phone number already registered.")
            else:
                user = User.objects.create_user(username=u, password=p, email=e)
                UserProfile.objects.create(user=user, phone_number=phone)
                user = authenticate(request, username=u, password=p)
                if user:
                    login(request, user)
                    messages.success(request, "Account created. You are now logged in.")
                    return redirect("predict")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


# ------- Spike-rule helper -------
def is_spike_for_user(user, current_amount: Decimal):
    """
    True if current_amount >> avg of last N txns by this user.
    """
    N = int(getattr(settings, "RULE_LAST_N", 4))
    MIN_PREV = int(getattr(settings, "RULE_MIN_PREV", 3))
    MULT = float(getattr(settings, "RULE_MULTIPLIER", 3.0))
    MIN_DELTA = float(getattr(settings, "RULE_MIN_DELTA", 500.0))

    recent = list(
        Transaction.objects.filter(user=user)
        .order_by("-created_at")
        .values_list("amt", flat=True)[:N]
    )
    if len(recent) < MIN_PREV:
        return False, 0.0, MULT, MIN_DELTA

    avg = float(sum([float(a) for a in recent]) / len(recent))
    curr = float(current_amount)
    spike = (avg > 0.0) and (curr > avg * MULT) and ((curr - avg) >= MIN_DELTA)
    return spike, avg, MULT, MIN_DELTA


# ------- Main submit form (logged-in only) -------
@login_required
def predict_view(request):
    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            phone = cd["phone_number"].strip()

            hour = cd["hour_time"].hour
            dow = datetime.now().weekday()

            # Minimal feature payload (matches minimal model)
            payload = {
                "category": cd["category"],
                "amt": float(cd["amt"]),
                "city": cd["city"],
                "state": cd["state"],
                "job": cd["job"],
                "hour": int(hour),
                "dow": int(dow),
                "age": int(cd["age"]),
            }

            # ML score (robust to errors)
            try:
                prob = float(score_transaction(payload))
            except Exception as e:
                prob = 0.0
                messages.error(request, f"Model error: {e}")
                # Continue; we still store the transaction

            # Rule: spike vs last N user txns
            spike, avg_last_n, mult_used, delta_used = is_spike_for_user(request.user, cd["amt"])

            # Combine decisions
            is_risky = (prob >= settings.FRAUD_THRESHOLD) or spike

            # Persist transaction (always)
            txn = Transaction.objects.create(
                user=request.user,
                category=cd["category"],
                amt=cd["amt"],
                city=cd["city"],
                state=cd["state"],
                job=cd["job"],
                hour=hour,
                dow=dow,
                age=cd["age"],
                ml_prob=float(prob),
                rule_avg_last_n=(avg_last_n or None),
                rule_multiplier_used=mult_used,
                rule_delta_used=delta_used,
                rule_flag=bool(spike),
                otp_required=is_risky,
                final_decision=("challenge" if is_risky else "allowed"),
            )

            if is_risky:
                try:
                    otp_id = send_otp(phone)
                except (HTTPError, RequestException) as e:
                    # Could not send OTP — block the txn
                    txn.final_decision = "blocked"
                    txn.notes = f"OTP send failed: {e}"
                    txn.save(update_fields=["final_decision", "notes"])
                    messages.error(request, f"Could not send OTP: {e}")
                    return render(request, "predict.html", {"form": form, "prob": prob, "allowed": False})

                txn.otp_id = otp_id
                txn.save(update_fields=["otp_id"])

                # Remember which txn we're verifying
                request.session["last_txn_id"] = txn.id
                request.session["otp_id"] = otp_id
                request.session["phone_number"] = phone
                request.session["fraud_prob"] = prob
                messages.warning(request, f"⚠️ Suspicious transaction (p={prob:.2f}). OTP sent.")
                return redirect("verify_otp")
            else:
                messages.success(request, f"✅ Allowed (fraud prob={prob:.2f}).")
                return render(request, "predict.html", {"form": form, "prob": prob, "allowed": True})

        else:
            # Invalid form – show errors
            print("FORM ERRORS:", form.errors.as_json())
            messages.error(request, "Please fix the errors below.")
            return render(request, "predict.html", {"form": form})
    else:
        form = TransactionForm()

    return render(request, "predict.html", {"form": form})


# ------- OTP verification (updates the stored txn) -------
@login_required
def verify_otp_view(request):
    otp_id = request.session.get("otp_id")
    txn_id = request.session.get("last_txn_id")
    if not otp_id or not txn_id:
        messages.error(request, "No OTP in progress. Please submit a transaction first.")
        return redirect("predict")

    txn = Transaction.objects.filter(id=txn_id, user=request.user).first()
    if not txn:
        messages.error(request, "Transaction not found.")
        return redirect("predict")

    if request.method == "POST":
        form = OTPForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["otp_code"]
            try:
                valid = verify_otp(otp_id, code)
            except (HTTPError, RequestException) as e:
                messages.error(request, f"OTP verification error: {e}")
                return render(request, "verify_otp.html", {"form": form})

            if valid:
                txn.otp_verified = True
                txn.final_decision = "approved"
                txn.save(update_fields=["otp_verified", "final_decision"])
                # clear session context
                for k in ["otp_id", "last_txn_id", "phone_number", "fraud_prob"]:
                    request.session.pop(k, None)
                messages.success(request, "✅ OTP verified. Transaction approved.")
                return redirect("predict")
            else:
                txn.final_decision = "blocked"
                txn.save(update_fields=["final_decision"])
                messages.error(request, "❌ Incorrect/expired OTP. Transaction blocked.")
                return redirect("predict")
    else:
        form = OTPForm()

    return render(request, "verify_otp.html", {"form": form})


# ------- Simple history page -------
@login_required
def transactions_view(request):
    txns = Transaction.objects.filter(user=request.user)[:50]
    return render(request, "transactions.html", {"txns": txns})
