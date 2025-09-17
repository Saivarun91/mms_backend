from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_matgattribute, name='create_matgattribute'),
    path('list/', views.list_matgattributes, name='list_matgattributes'),
    path('update/<int:attrib_id>/', views.update_matgattribute, name='update_matgattribute'),
    path('delete/<int:attrib_id>/', views.delete_matgattribute, name='delete_matgattribute'),
]
