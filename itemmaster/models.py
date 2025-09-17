# from django.db import models
# from django.conf import settings
# from django.utils import timezone
# from Employee.models import Employee

# class ItemMaster(models.Model):
#     local_item_id = models.AutoField(primary_key=True)
#     sap_item_id = models.IntegerField(
#         null=True, blank=True, help_text="Number assigned by SAP"
#     )
#     mat_type_code = models.CharField(max_length=4)   # FK to MaterialTypes
#     mgrp_code = models.CharField(max_length=9)       # FK to MatGroups
#     item_desc = models.CharField(max_length=40)
#     notes = models.CharField(max_length=250, blank=True, null=True)
#     search_text = models.CharField(
#         max_length=300,
#         blank=True,
#         null=True,
#         help_text="Concatenated searchable text"
#     )

#     created = models.DateTimeField(auto_now_add=True)
#     createdby = models.ForeignKey(
#         Employee,
#         related_name="itemmaster_created",
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True
#     )
#     updated = models.DateTimeField(default=timezone.now)
#     updatedby = models.ForeignKey(
#         Employee,
#         related_name="itemmaster_updated",
#         on_delete=models.CASCADE,
#         null=True,
#         blank=True
#     )
#     is_deleted = models.BooleanField(default=False)

#     def __str__(self):
#         return f"{self.local_item_id} - {self.item_desc}"
from django.db import models
from django.utils import timezone
from Employee.models import Employee


class ItemMaster(models.Model):
    local_item_id = models.AutoField(primary_key=True)
    sap_item_id = models.IntegerField(null=True, blank=True)
    mat_type_code = models.ForeignKey(
        "MaterialType.MaterialType",
        to_field="mat_type_code",
        db_column="mat_type_code",
        on_delete=models.CASCADE,
        related_name="items"
    )
    mgrp_code = models.ForeignKey(
        "matgroups.MatGroup",
        to_field="mgrp_code",
        db_column="mgrp_code",
        on_delete=models.CASCADE,
        related_name="items"
    )
    item_desc = models.CharField(max_length=40)
    notes = models.CharField(max_length=250, blank=True, null=True)
    search_text = models.CharField(max_length=300, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    createdby = models.ForeignKey(
        Employee,
        related_name="itemmaster_created",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    updated = models.DateTimeField(default=timezone.now)
    updatedby = models.ForeignKey(
        Employee,
        related_name="itemmaster_updated",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.local_item_id} - {self.item_desc}"
