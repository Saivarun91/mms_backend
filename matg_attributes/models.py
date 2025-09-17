from django.db import models
from django.utils import timezone
from Employee.models import Employee  # ✅ Import Employee model

class MatgAttribute(models.Model):
    attrib_id = models.AutoField(primary_key=True)
    mgrp_code = models.ForeignKey("matgroups.MatGroup", on_delete=models.CASCADE, related_name="attributes")
    attrib_printpriority = models.IntegerField(default=0, help_text="Lower value appears earlier in item name")
    attrib_name = models.CharField(max_length=30)
    attrib_printname = models.CharField(max_length=10)
    attrib_name_validation = models.CharField(max_length=30, blank=True)
    att_maxnamelen = models.PositiveSmallIntegerField(null=True, blank=True)
    attrib_tagname = models.CharField(max_length=10)
    attrib_tag_validation = models.CharField(max_length=30, blank=True)
    attrib_maxtaglen = models.PositiveSmallIntegerField(null=True, blank=True)

    # ✅ Audit fields changed to Employee
    created = models.DateTimeField(auto_now_add=True)
    createdby = models.ForeignKey(Employee, related_name="matgattr_created",
                                   on_delete=models.SET_NULL, null=True, blank=True)
    updated = models.DateTimeField(default=timezone.now)
    updatedby = models.ForeignKey(Employee, related_name="matgattr_updated",
                                   on_delete=models.SET_NULL, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.attrib_name} ({self.mgrp_code_id})"
