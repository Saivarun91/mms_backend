from django.db import models
from django.conf import settings
from django.utils import timezone
from Employee.models import Employee

class MatGroup(models.Model):
    mgrp_code = models.CharField(max_length=30, primary_key=True)
    sgrp_code = models.ForeignKey("supergroups.SuperGroup", on_delete=models.CASCADE, related_name="matgroups",blank=True, null=True)
    is_service = models.BooleanField(default=False)
    mgrp_shortname = models.CharField(max_length=150,null=True, blank=True)
    mgrp_longname = models.CharField(max_length=150,null=True, blank=True)
    attribgrpid = models.IntegerField(null=True, blank=True)  # FK to Attributes (optional)
    # attribgrpid = models.ForeignKey(
    #     "matg_attributes.MatgAttribute",   # use app_label.ModelName
    #     on_delete=models.SET_NULL,       # don't delete group if attribute deleted
    #     related_name="matgroups",
    #     null=True,
    #     blank=True
    # ) # FK to Attributes (optional) 
    notes = models.CharField(max_length=250, blank=True)

    created = models.DateTimeField(default=timezone.now)
    createdby = models.ForeignKey(Employee, related_name="matgroup_created",
                                  on_delete=models.SET_NULL, null=True, blank=True)
    updated = models.DateTimeField(default=timezone.now)  
    updatedby = models.ForeignKey(Employee, related_name="matgroup_updated",
                                  on_delete=models.SET_NULL, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.mgrp_shortname