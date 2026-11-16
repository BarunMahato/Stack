from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    CurrentUserProfileAPIView,
    LogoutAPIView,
    RegisterAPIView,
    UserDetailAPIView,
    UserListCreateAPIView,
)

app_name = "users"

urlpatterns = [
    # Auth & JWT Token Endpoints
    path("auth/register/", RegisterAPIView.as_view(), name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", LogoutAPIView.as_view(), name="logout"),
    path("auth/me/", CurrentUserProfileAPIView.as_view(), name="current-user-profile"),

    # Librarian User Management Endpoints
    path("", UserListCreateAPIView.as_view(), name="user-list-create"),
    path("<int:pk>/", UserDetailAPIView.as_view(), name="user-detail"),
]