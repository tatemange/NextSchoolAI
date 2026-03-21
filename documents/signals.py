"""
Signals de l'application documents — NextSchoolAI.
Déclenche automatiquement l'analyse IA après l'upload d'un document.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='documents.Document')
def analyser_document_apres_upload(sender, instance, created, **kwargs):
    """
    Signal déclenché après la création d'un document.
    Lance automatiquement l'analyse IA et met à jour le statut.
    """
    if not created:
        return
    if instance.statut_doc != 'brouillon':
        return

    try:
        from ia.services import IAService
        nouveau_statut = IAService.analyser_document(instance)
        # Mise à jour sans déclencher à nouveau le signal
        sender.objects.filter(pk=instance.pk).update(statut_ia=nouveau_statut)
        logger.info(f"[Signal] Document {instance.pk} analysé → statut_ia = {nouveau_statut}")
    except Exception as e:
        logger.error(f"[Signal] Erreur analyse IA document {instance.pk}: {e}")
        sender.objects.filter(pk=instance.pk).update(statut_ia='rejete')
