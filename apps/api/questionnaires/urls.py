from django.urls import path
from .views import QuestionnaireList, QuestionList, DraftAnswer, ApproveAnswer

urlpatterns = [path("", QuestionnaireList.as_view()), path("questions/", QuestionList.as_view()), path("questions/<uuid:question_id>/draft/", DraftAnswer.as_view()), path("answers/<uuid:answer_id>/approve/", ApproveAnswer.as_view())]
