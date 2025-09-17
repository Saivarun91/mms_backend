from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('list/', views.list_employees, name='employee-list'),
    path('update/<int:emp_id>/', views.update_employee, name='employee-update'),
    path('delete/<int:emp_id>/', views.delete_employee, name='employee-delete'),
    path('verify_email_otp/', views.verify_email_otp, name='verify-email-otp'),
    path('verify_phone_otp/', views.verify_phone_otp),
    # 🔹 New endpoints
    path('without-role/', views.list_employees_without_role,
         name='employee-without-role'),
    path('assign-role/<int:emp_id>/', views.assign_role,
         name='employee-assign-role'),
    path('bulk-assign-role/', views.bulk_assign_roles,
         name='employee-bulk-assign-role'),  # 👈 New
]
