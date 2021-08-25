from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("redirect/", views.redirect_to_ui, name="index"),
]
