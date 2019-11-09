from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse

from rest_framework.authtoken.models import Token


def index(request):
    return HttpResponse("Share all the bikes \o/")


def redirect_to_ui(request):
    if request.user.is_authenticated:
        token, created = Token.objects.get_or_create(user=request.user)
        return redirect('{url}/login/return?token={token}'.format(
            url=settings.UI_URL, token=token.key
        ))

    return redirect(settings.UI_URL)
