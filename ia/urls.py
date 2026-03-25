"""URLs de l'application ia — NextSchoolAI."""

from django.urls import path
from . import views

app_name = 'ia'

urlpatterns = [
    path('document/<int:doc_pk>/resumer/', views.resumer_document, name='resumer'),
    path('document/<int:doc_pk>/chat/',    views.chat_document_ajax, name='chat_ajax'),
]
