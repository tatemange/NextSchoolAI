"""
URL principale du projet NextSchoolAI.
Inclut toutes les applications modulaires.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Page d'accueil temporaire (redirige vers la liste des documents)
from django.shortcuts import redirect

urlpatterns = [
    # Administration Django
    path('admin/', admin.site.urls),

    # Page d'accueil → bibliothèque
    path('', lambda req: redirect('documents:liste'), name='accueil'),

    # Applications
    path('comptes/',     include('accounts.urls',   namespace='accounts')),
    path('documents/',   include('documents.urls',  namespace='documents')),
    path('qcm/',         include('quiz.urls',        namespace='quiz')),
    path('ia/',          include('ia.urls',          namespace='ia')),
]

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,  document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personnalisation de l'interface admin
admin.site.site_header  = "NextSchoolAI — Administration"
admin.site.site_title   = "NextSchoolAI Admin"
admin.site.index_title  = "Tableau de bord d'administration"
