from django.urls import path
from . import views

urlpatterns = [
    path('bulk-upload/', views.bulk_upload, name='bulk_upload'),
    path('get-fields/', views.get_model_fields, name='get_model_fields'),
]
