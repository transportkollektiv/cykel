from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.timezone import now, timedelta
from rest_framework.authtoken.models import Token
from bikesharing.models import Bike, VehicleType
from reservation.models import Reservation

def index(request):
    return HttpResponse("Share all the bikes \\o/")


def redirect_to_ui(request):
    if request.user.is_authenticated:
        token, created = Token.objects.get_or_create(user=request.user)
        return redirect(
            "{url}/login/return?token={token}".format(
                url=settings.UI_URL, token=token.key
            )
        )

    return redirect(settings.UI_URL)
