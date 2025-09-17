from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
import json
from .models import MatGroup
from supergroups.models import SuperGroup
from Employee.models import Employee
from Common.Middleware import authenticate, restrict


# ✅ Helper to get employee name
def get_employee_name(emp):
    return emp.emp_name if emp else None


# ✅ CREATE MatGroup
@csrf_exempt
@authenticate
@restrict(roles=["Admin", "SuperAdmin","MDGT"])
def create_matgroup(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))

            mgrp_code = data.get("mgrp_code")
            sgrp_code = data.get("sgrp_code",None)
            mgrp_shortname = data.get("mgrp_shortname",None)
            mgrp_longname = data.get("mgrp_longname",None)
            is_service = data.get("is_service", False)
            attribgrpid = data.get("attribgrpid","")
            notes = data.get("notes", "")

            if not mgrp_code:
                return JsonResponse({"error": "Required fields: mgrp_code, sgrp_code, mgrp_shortname, mgrp_longname"}, status=400)

            # ✅ Check if SuperGroup exists
            supergroup = SuperGroup.objects.filter(sgrp_code=sgrp_code, is_deleted=False).first()
            # if not supergroup:
            #     return JsonResponse({"error": "SuperGroup not found"}, status=404)

            # ✅ Get Employee for createdby
            emp_id = request.user.get("emp_id")
            createdby = Employee.objects.filter(emp_id=emp_id).first()

            matgroup = MatGroup.objects.create(
                mgrp_code=mgrp_code,
                sgrp_code=supergroup,
                is_service=is_service,
                mgrp_shortname=mgrp_shortname,
                mgrp_longname=mgrp_longname,
                attribgrpid=attribgrpid,
                notes=notes,
                createdby=createdby,
                updatedby=createdby
            )

            response_data = {
                "mgrp_code": matgroup.mgrp_code,
                "mgrp_shortname": matgroup.mgrp_shortname,
                "mgrp_longname": matgroup.mgrp_longname,
                "is_service": matgroup.is_service,
                "attribgrpid": matgroup.attribgrpid,
                "notes": matgroup.notes,
                "supergroup": matgroup.sgrp_code.sgrp_name,
                "created": matgroup.created.strftime("%Y-%m-%d %H:%M:%S"),
                "updated": matgroup.updated.strftime("%Y-%m-%d %H:%M:%S"),
                "createdby": get_employee_name(matgroup.createdby),
                "updatedby": get_employee_name(matgroup.updatedby)
            }
            return JsonResponse(response_data, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# ✅ LIST MatGroups
@authenticate
@restrict(roles=["Admin", "SuperAdmin", "User","MDGT"])
def list_matgroups(request):
    if request.method == "GET":
        matgroups = MatGroup.objects.filter(is_deleted=False)
        response_data = []
        for mg in matgroups:
            response_data.append({
                "mgrp_code": mg.mgrp_code,
                "mgrp_shortname": mg.mgrp_shortname,
                "mgrp_longname": mg.mgrp_longname,
                "is_service": mg.is_service,
                "attribgrpid": mg.attribgrpid,
                "notes": mg.notes,
                "supergroup": mg.sgrp_code.sgrp_name if mg.sgrp_code else None,
                "created": mg.created.strftime("%Y-%m-%d %H:%M:%S"),
                "updated": mg.updated.strftime("%Y-%m-%d %H:%M:%S"),
                "createdby": get_employee_name(mg.createdby),
                "updatedby": get_employee_name(mg.updatedby)
            })
        return JsonResponse(response_data, safe=False)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# ✅ UPDATE MatGroup
@csrf_exempt
@authenticate
@restrict(roles=["Admin", "SuperAdmin","MDGT"])
def update_matgroup(request, mgrp_code):
    if request.method == "PUT":
        try:
            data = json.loads(request.body.decode("utf-8"))

            matgroup = MatGroup.objects.filter(mgrp_code=mgrp_code, is_deleted=False).first()
            if not matgroup:
                return JsonResponse({"error": "MatGroup not found"}, status=404)

            # ✅ Update fields
            matgroup.mgrp_shortname = data.get("mgrp_shortname", matgroup.mgrp_shortname)
            matgroup.mgrp_longname = data.get("mgrp_longname", matgroup.mgrp_longname)
            matgroup.is_service = data.get("is_service", matgroup.is_service)
            matgroup.attribgrpid = data.get("attribgrpid", matgroup.attribgrpid)
            matgroup.notes = data.get("notes", matgroup.notes)

            # ✅ If sgrp_code is updated
            new_sgrp_code = data.get("sgrp_code")
            if new_sgrp_code:
                supergroup = SuperGroup.objects.filter(sgrp_code=new_sgrp_code, is_deleted=False).first()
                if not supergroup:
                    return JsonResponse({"error": "SuperGroup not found"}, status=404)
                matgroup.sgrp_code = supergroup

            # ✅ Update audit
            emp_id = request.user.get("emp_id")
            updatedby = Employee.objects.filter(emp_id=emp_id).first()
            matgroup.updatedby = updatedby
            matgroup.updated = timezone.now()

            matgroup.save()

            response_data = {
                "mgrp_code": matgroup.mgrp_code,
                "mgrp_shortname": matgroup.mgrp_shortname,
                "mgrp_longname": matgroup.mgrp_longname,
                "is_service": matgroup.is_service,
                "attribgrpid": matgroup.attribgrpid,
                "notes": matgroup.notes,
                "supergroup": matgroup.sgrp_code.sgrp_name,
                "created": matgroup.created.strftime("%Y-%m-%d %H:%M:%S"),
                "updated": matgroup.updated.strftime("%Y-%m-%d %H:%M:%S"),
                "createdby": get_employee_name(matgroup.createdby),
                "updatedby": get_employee_name(matgroup.updatedby)
            }
            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


# ✅ HARD DELETE MatGroup
@csrf_exempt
@authenticate
@restrict(roles=["Admin", "SuperAdmin","MDGT"])
def delete_matgroup(request, mgrp_code):
    if request.method == "DELETE":
        matgroup = MatGroup.objects.filter(mgrp_code=mgrp_code).first()
        if not matgroup:
            return JsonResponse({"error": "MatGroup not found"}, status=404)

        matgroup.delete()  # ✅ Hard delete
        return JsonResponse({"message": "MatGroup deleted successfully"}, status=200)

    return JsonResponse({"error": "Invalid request method"}, status=405)
