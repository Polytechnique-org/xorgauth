from django.conf import settings


def maintenance(request):
    """Export settings.MAINTENANCE to templates"""
    return {
        'MAINTENANCE': settings.MAINTENANCE,
    }
