from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
import json
from .models import MatgAttribute
from matgroups.models import MatGroup
from Employee.models import Employee
from Common.Middleware import authenticate, restrict


# ✅ Helper function to get employee name
def get_employee_name(emp):
    return emp.emp_name if emp else None


# ✅ CREATE MatgAttribute
@csrf_exempt
@authenticate
@restrict(roles=["Admin", "SuperAdmin",'MDGT'])
def create_matgattribute(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            mgrp_code = data.get("mgrp_code")
            attrib_printpriority = data.get("attrib_printpriority", 0)
            attrib_name = data.get("attrib_name")
            attrib_printname = data.get("attrib_printname")
            attrib_name_validation = data.get("attrib_name_validation", "")
            att_maxnamelen = data.get("att_maxnamelen")
            attrib_tagname = data.get("attrib_tagname")
            attrib_tag_validation = data.get("attrib_tag_validation", "")
            attrib_maxtaglen = data.get("attrib_maxtaglen")

            # ✅ Check required fields
            if not mgrp_code or not attrib_name or not attrib_printname or not attrib_tagname:
                return JsonResponse({"error": "Required fields: mgrp_code, attrib_name, attrib_printname, attrib_tagname"}, status=400)

            # ✅ Check if MatGroup exists
            matgroup = MatGroup.objects.filter(mgrp_code=mgrp_code, is_deleted=False).first()
            if not matgroup:
                return JsonResponse({"error": "MatGroup not found"}, status=404)

            # ✅ Get Employee for createdby
            emp_id = request.user.get("emp_id")
            createdby = Employee.objects.filter(emp_id=emp_id).first()

            # ✅ Create MatgAttribute
            attribute = MatgAttribute.objects.create(
                mgrp_code=matgroup,
                attrib_printpriority=attrib_printpriority,
                attrib_name=attrib_name,
                attrib_printname=attrib_printname,
                attrib_name_validation=attrib_name_validation,
                att_maxnamelen=att_maxnamelen,
                attrib_tagname=attrib_tagname,
                attrib_tag_validation=attrib_tag_validation,
                attrib_maxtaglen=attrib_maxtaglen,
                createdby=createdby,
                updatedby=createdby
            )

            response_data = {
                "attrib_id": attribute.attrib_id,
                "mgrp_code": attribute.mgrp_code.mgrp_code,
                "attrib_name": attribute.attrib_name,
                "attrib_printname": attribute.attrib_printname,
                "attrib_tagname": attribute.attrib_tagname,
                "attrib_printpriority": attribute.attrib_printpriority,
                "attrib_name_validation": attribute.attrib_name_validation,
                "att_maxnamelen": attribute.att_maxnamelen,
                "attrib_tag_validation": attribute.attrib_tag_validation,
                "attrib_maxtaglen": attribute.attrib_maxtaglen,
                "created": attribute.created.strftime("%Y-%m-%d %H:%M:%S"),
                "updated": attribute.updated.strftime("%Y-%m-%d %H:%M:%S"),
                "createdby": get_employee_name(attribute.createdby),
                "updatedby": get_employee_name(attribute.updatedby)
            }
            return JsonResponse(response_data, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# ✅ LIST MatgAttributes
@authenticate
@restrict(roles=["Admin", "SuperAdmin", "User","MDGT"])
def list_matgattributes(request):
    if request.method == "GET":
        attributes = MatgAttribute.objects.filter(is_deleted=False)
        response_data = []
        for attr in attributes:
            response_data.append({
                "attrib_id": attr.attrib_id,
                "mgrp_code": attr.mgrp_code.mgrp_code if attr.mgrp_code else None,
                "attrib_name": attr.attrib_name,
                "attrib_printname": attr.attrib_printname,
                "attrib_tagname": attr.attrib_tagname,
                "attrib_printpriority": attr.attrib_printpriority,
                "attrib_name_validation": attr.attrib_name_validation,
                "att_maxnamelen": attr.att_maxnamelen,
                "attrib_tag_validation": attr.attrib_tag_validation,
                "attrib_maxtaglen": attr.attrib_maxtaglen,
                "created": attr.created.strftime("%Y-%m-%d %H:%M:%S"),
                "updated": attr.updated.strftime("%Y-%m-%d %H:%M:%S"),
                "createdby": get_employee_name(attr.createdby),
                "updatedby": get_employee_name(attr.updatedby)
            })
        return JsonResponse(response_data, safe=False)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# ✅ UPDATE MatgAttribute
@csrf_exempt
@authenticate
@restrict(roles=["Admin", "SuperAdmin","MDGT"])
def update_matgattribute(request, attrib_id):
    if request.method == "PUT":
        try:
            data = json.loads(request.body.decode("utf-8"))

            attribute = MatgAttribute.objects.filter(attrib_id=attrib_id, is_deleted=False).first()
            if not attribute:
                return JsonResponse({"error": "MatgAttribute not found"}, status=404)

            # ✅ Update fields
            attribute.attrib_printpriority = data.get("attrib_printpriority", attribute.attrib_printpriority)
            attribute.attrib_name = data.get("attrib_name", attribute.attrib_name)
            attribute.attrib_printname = data.get("attrib_printname", attribute.attrib_printname)
            attribute.attrib_name_validation = data.get("attrib_name_validation", attribute.attrib_name_validation)
            attribute.att_maxnamelen = data.get("att_maxnamelen", attribute.att_maxnamelen)
            attribute.attrib_tagname = data.get("attrib_tagname", attribute.attrib_tagname)
            attribute.attrib_tag_validation = data.get("attrib_tag_validation", attribute.attrib_tag_validation)
            attribute.attrib_maxtaglen = data.get("attrib_maxtaglen", attribute.attrib_maxtaglen)

            # ✅ If mgrp_code is updated
            new_mgrp_code = data.get("mgrp_code")
            if new_mgrp_code:
                matgroup = MatGroup.objects.filter(mgrp_code=new_mgrp_code, is_deleted=False).first()
                if not matgroup:
                    return JsonResponse({"error": "MatGroup not found"}, status=404)
                attribute.mgrp_code = matgroup

            # ✅ Update audit
            emp_id = request.user.get("emp_id")
            updatedby = Employee.objects.filter(emp_id=emp_id).first()
            attribute.updatedby = updatedby
            attribute.updated = timezone.now()

            attribute.save()

            response_data = {
                "attrib_id": attribute.attrib_id,
                "mgrp_code": attribute.mgrp_code.mgrp_code,
                "attrib_name": attribute.attrib_name,
                "attrib_printname": attribute.attrib_printname,
                "attrib_tagname": attribute.attrib_tagname,
                "attrib_printpriority": attribute.attrib_printpriority,
                "attrib_name_validation": attribute.attrib_name_validation,
                "att_maxnamelen": attribute.att_maxnamelen,
                "attrib_tag_validation": attribute.attrib_tag_validation,
                "attrib_maxtaglen": attribute.attrib_maxtaglen,
                "created": attribute.created.strftime("%Y-%m-%d %H:%M:%S"),
                "updated": attribute.updated.strftime("%Y-%m-%d %H:%M:%S"),
                "createdby": get_employee_name(attribute.createdby),
                "updatedby": get_employee_name(attribute.updatedby)
            }
            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# ✅ HARD DELETE MatgAttribute
@csrf_exempt
@authenticate
@restrict(roles=["Admin", "SuperAdmin","MDGT"])
def delete_matgattribute(request, attrib_id):
    if request.method == "DELETE":
        attribute = MatgAttribute.objects.filter(attrib_id=attrib_id).first()
        if not attribute:
            return JsonResponse({"error": "MatgAttribute not found"}, status=404)

        attribute.delete()  # ✅ Hard delete
        return JsonResponse({"message": "MatgAttribute deleted successfully"}, status=200)

    return JsonResponse({"error": "Invalid request method"}, status=405)
