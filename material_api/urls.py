from django.urls import path
from . import views

urlpatterns = [
    # 🔹 1. Search MatGroups by description (POST)
    path('matgroups/search/', views.search_groups, name='search_groups'),

    # 🔹 2. Get Materials inside a selected group (GET)
    path('matgroups/<str:group_code>/materials/', views.materials_by_group, name='materials_by_group'),

    # 🔹 3. Get Items inside a selected group (GET)
    path('matgroups/<str:group_code>/items/', views.items_by_group, name='items_by_group'),

    path('matgroups/<str:group_code>/items/sap_ids/', views.sap_ids_by_matgroup, name='sap_ids_by_matgroup'),
    # 🔹 4. Get Items by group + material type (GET)
    path('matgroups/<str:group_code>/items/<str:mat_type_code>/', views.items_by_group_and_type, name='items_by_group_and_type'),


]
