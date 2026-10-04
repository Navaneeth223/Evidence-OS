from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from core.views import health, register, me, organizations
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls), path("health/", health), path("ready/", health),
    path("api/auth/register/", register), path("api/auth/me/", me), path("api/organizations/", organizations),
    path("api/auth/token/", TokenObtainPairView.as_view()), path("api/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/evidence/", include("evidence.urls")), path("api/questionnaires/", include("questionnaires.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"), path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
