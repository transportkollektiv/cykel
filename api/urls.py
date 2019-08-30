"""cykel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf.urls import url, include
from rest_framework import routers, serializers, viewsets
from rest_framework.urlpatterns import format_suffix_patterns

from .views import BikeViewSet
from .views import StationViewSet
from .views import CurrentRentViewSet
from .views import updatebikelocation
from .views import start_rent
from .views import finish_rent
from .views import UserDetailsView

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
#router.register(r'bikes', BikeViewSet)
#router.register(r'stations', StationViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api/', include('rest_framework.urls', namespace='rest_framework_api')),
    path('bike/updatelocation', updatebikelocation),
    path('rent/start', start_rent),
    path('rent/finish', finish_rent),
    path('rent/current', CurrentRentViewSet.as_view({'get': 'list'})),
    path('user', UserDetailsView.as_view()),
]
