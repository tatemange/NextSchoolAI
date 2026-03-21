"""
Vues de l'application accounts — NextSchoolAI.
Inscription, connexion, déconnexion, tableau de bord, profil.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q
from .forms import InscriptionForm, ConnexionForm, ProfilForm


# =============================================================================
# INSCRIPTION
# =============================================================================

@require_http_methods(["GET", "POST"])
def inscription(request):
    """Inscription d'un nouvel utilisateur."""
    if request.user.is_authenticated:
        return redirect('accounts:tableau_de_bord')

    form = InscriptionForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        utilisateur = form.save()
        login(request, utilisateur)
        messages.success(
            request,
            _("Bienvenue sur NextSchoolAI, %(prenom)s ! Votre compte a été créé avec succès.") % {
                'prenom': utilisateur.first_name or utilisateur.username
            }
        )
        return redirect('accounts:tableau_de_bord')

    return render(request, 'accounts/inscription.html', {'form': form, 'titre_page': "Créer un compte"})


# =============================================================================
# CONNEXION
# =============================================================================

@require_http_methods(["GET", "POST"])
def connexion(request):
    """Connexion d'un utilisateur existant."""
    if request.user.is_authenticated:
        return redirect('accounts:tableau_de_bord')

    form = ConnexionForm(request.POST or None)
    if form.is_valid():
        utilisateur = form.cleaned_data['utilisateur']
        # Gestion de "rester connecté"
        if not form.cleaned_data.get('se_souvenir'):
            request.session.set_expiry(0)  # Session fermée à la fermeture du navigateur
        login(request, utilisateur)
        messages.success(
            request,
            _("Bonne reprise, %(prenom)s !") % {'prenom': utilisateur.first_name or utilisateur.username}
        )
        # Redirection vers la page demandée ou le tableau de bord
        next_url = request.GET.get('next', 'accounts:tableau_de_bord')
        return redirect(next_url)

    return render(request, 'accounts/connexion.html', {'form': form, 'titre_page': "Connexion"})


# =============================================================================
# DÉCONNEXION
# =============================================================================

@login_required
def deconnexion(request):
    """Déconnexion de l'utilisateur."""
    logout(request)
    messages.info(request, _("Vous avez été déconnecté. À bientôt !"))
    return redirect('accounts:connexion')


# =============================================================================
# TABLEAU DE BORD
# =============================================================================

@login_required
def tableau_de_bord(request):
    """
    Tableau de bord personnalisé selon le rôle de l'utilisateur.
    - Apprenant : historique activités, scores QCM, documents récents
    - Enseignant : mes documents uploadés, en attente de validation
    - Admin     : statistiques globales, modération
    """
    from documents.models import Document, Activite
    from quiz.models import SessionQCM

    utilisateur = request.user
    contexte    = {
        'titre_page':  "Tableau de bord",
        'utilisateur': utilisateur,
    }

    if utilisateur.est_apprenant:
        # Historique des activités récentes
        activites_recentes = Activite.objects.filter(
            utilisateur=utilisateur
        ).select_related('document').order_by('-date_action')[:10]

        # Sessions QCM récentes
        sessions_qcm = SessionQCM.objects.filter(
            utilisateur=utilisateur,
            statut='termine'
        ).order_by('-date_debut')[:5]

        # Score moyen
        from django.db.models import Avg
        score_moyen = SessionQCM.objects.filter(
            utilisateur=utilisateur,
            statut='termine',
            score_total__gt=0
        ).aggregate(
            avg_pct=Avg('score_obtenu')
        )

        contexte.update({
            'activites_recentes': activites_recentes,
            'sessions_qcm':       sessions_qcm,
            'nb_sessions':        SessionQCM.objects.filter(utilisateur=utilisateur).count(),
        })

    elif utilisateur.est_enseignant:
        # Documents uploadés par l'enseignant
        mes_documents = Document.objects.filter(
            utilisateur=utilisateur
        ).order_by('-date_upload')[:10]

        contexte.update({
            'mes_documents':      mes_documents,
            'nb_en_attente':      Document.objects.filter(utilisateur=utilisateur, statut_doc='brouillon').count(),
            'nb_publies':         Document.objects.filter(utilisateur=utilisateur, statut_doc='publie').count(),
            'nb_rejetes':         Document.objects.filter(utilisateur=utilisateur, statut_doc='rejete').count(),
        })

    elif utilisateur.est_admin:
        # Statistiques globales pour l'administrateur
        contexte.update({
            'nb_utilisateurs':     utilisateur.__class__.objects.count(),
            'nb_documents':        Document.objects.count(),
            'nb_en_attente_valid': Document.objects.filter(statut_ia='valide', statut_humain=False).count(),
            'nb_documents_publies': Document.objects.filter(statut_doc='publie').count(),
        })

    return render(request, 'accounts/tableau_de_bord.html', contexte)


# =============================================================================
# PROFIL
# =============================================================================

@login_required
def profil(request):
    """Affichage et modification du profil utilisateur."""
    form = ProfilForm(request.POST or None, request.FILES or None, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, _("Votre profil a été mis à jour avec succès."))
        return redirect('accounts:profil')

    return render(request, 'accounts/profil.html', {'form': form, 'titre_page': "Mon profil"})


# =============================================================================
# SET THEME (AJAX)
# =============================================================================

@login_required
@require_http_methods(["POST"])
def set_theme(request):
    """Sauvegarde le thème visuel choisi par l'utilisateur."""
    from django.http import JsonResponse
    from .models import Utilisateur

    VALID_THEMES = {'brownie', 'midnight', 'arctic', 'forest', 'ocean', 'rose'}
    theme = request.POST.get('theme', '').strip()

    if theme not in VALID_THEMES:
        return JsonResponse({'ok': False, 'error': 'Thème inconnu'}, status=400)

    request.user.theme = theme
    request.user.save(update_fields=['theme'])
    return JsonResponse({'ok': True, 'theme': theme})

