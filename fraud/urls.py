
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import register_view, predict_view, verify_otp_view, transactions_view

urlpatterns = [
    path("", predict_view, name="predict"),

    # auth
    path("register/", register_view, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    # app flows
    path("verify-otp/", verify_otp_view, name="verify_otp"),
    path("transactions/", transactions_view, name="transactions"),

    # optional: some redirects may point here; serve same login template
    path("accounts/login/", auth_views.LoginView.as_view(template_name="login.html")),
]


