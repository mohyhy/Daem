from django.utils import timezone

def refresh_session_activity(session):
    session.last_activity = timezone.now()
    session.save(update_fields=['last_activity'])
