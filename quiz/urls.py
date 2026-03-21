"""URLs de l'application quiz — NextSchoolAI."""

from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    path('document/<int:doc_pk>/generer/', views.generer_qcm,    name='generer'),
    path('session/<int:session_pk>/',      views.passer_qcm,     name='passer'),
    path('session/<int:session_pk>/soumettre/', views.soumettre_qcm, name='soumettre'),
    path('session/<int:session_pk>/resultats/', views.resultats_qcm, name='resultats'),
    path('session/<int:session_pk>/correction/', views.correction_qcm, name='correction'),
    path('historique/',                    views.historique_qcm, name='historique'),
]
