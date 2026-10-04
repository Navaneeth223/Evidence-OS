from django.urls import path
from .views import EvidenceList, EvidenceVerify, DocumentListCreate

urlpatterns = [path("", EvidenceList.as_view()), path("<uuid:pk>/verify/", EvidenceVerify.as_view()), path("documents/", DocumentListCreate.as_view())]
