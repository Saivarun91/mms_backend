from django.db import models
from django.utils import timezone
from Employee.models import Employee
from itemmaster.models import ItemMaster
from projects.models import Project


class Request(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("rejected", "Rejected"),
        ("closed", "Closed"),
    ]
    project_code = models.ForeignKey(
        Project, on_delete=models.CASCADE, null=True, blank=True)
    request_id = models.AutoField(primary_key=True)
    request_date = models.DateTimeField(default=timezone.now)
    request_status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="open")
    messages = models.JSONField(max_length=200, null=True, blank=True)
    request_data = models.JSONField(null=True, blank=True, default=dict)
    reply_emaildate = models.DateTimeField(null=True, blank=True)
    reply_smsdate = models.DateTimeField(null=True, blank=True)
    sap_item = models.ForeignKey(
        ItemMaster, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.CharField(max_length=100, blank=True)
    closetime = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, blank=True)
    timetaken = models.IntegerField(null=True, blank=True)

    # Audit fields
    created = models.DateTimeField(auto_now_add=True)
    createdby = models.ForeignKey(
        "Employee.Employee", related_name="requests_created", on_delete=models.CASCADE, null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)
    updatedby = models.ForeignKey(
       "Employee.Employee", related_name="requests_updated", on_delete=models.CASCADE, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"Request {self.request_id} - {self.request_status} - {self.project_code}"

