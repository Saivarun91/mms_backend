from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_request, name="create_request"),
    path("list/", views.list_requests, name="list_requests"),
    path("update/<int:request_id>/", views.update_request, name="update_request"),
    path("delete/<int:request_id>/", views.delete_request, name="delete_request"),
    path("assign-sap/<int:request_id>/", views.assign_sap_item, name="assign_sap_item"),  # ✅ New
]

