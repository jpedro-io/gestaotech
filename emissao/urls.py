from django.urls import path

from . import views

urlpatterns = [
    path("", views.emitir, name="emitir"),
    path("buscar/", views.buscar, name="buscar"),
    path("baixar/<str:token>/", views.baixar, name="baixar"),
    path("validar/", views.validar, name="validar"),
    path("validar/<str:codigo>/", views.validar, name="validar_codigo"),
]
