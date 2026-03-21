"""URLs de l'application documents — NextSchoolAI."""

from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('',                           views.liste_documents,    name='liste'),
    path('<int:pk>/',                  views.detail_document,    name='detail'),
    path('uploader/',                  views.uploader_document,  name='upload'),
    path('<int:pk>/telecharger/',      views.telecharger_document, name='telecharger'),
    path('<int:pk>/evaluer/',          views.evaluer_document,   name='evaluer'),
    path('mes-documents/',             views.mes_documents,      name='mes_documents'),
    path('moderation/',                views.moderation,         name='moderation'),
    path('<int:pk>/valider/',          views.valider_document,   name='valider'),
    path('<int:pk>/rejeter/',          views.rejeter_document,   name='rejeter'),
]
