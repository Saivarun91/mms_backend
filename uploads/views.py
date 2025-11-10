from django.shortcuts import render
import csv
import json
from django.apps import apps
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from Employee.models import Employee  # ✅ You already have this

# -------------------------
# 🔹 Helper: get model by name from any app
# -------------------------
def get_model_by_name(model_name):
    for model in apps.get_models():
        if model.__name__.lower() == model_name.lower():
            return model
    return None


# -------------------------
# 🔹 AJAX endpoint to get fields dynamically
# -------------------------
def get_model_fields(request):
    model_name = request.GET.get("model")
    Model = get_model_by_name(model_name)

    if not Model:
        return JsonResponse({"error": "Invalid model"}, status=400)

    fields = [f.name for f in Model._meta.fields if f.name != "id"]
    return JsonResponse({"fields": fields})


# -------------------------
# 🔹 Main view: upload JSON or CSV + bulk insert
# -------------------------
@csrf_exempt
def bulk_upload(request):
    """
    Supports both JSON and CSV uploads.
    Automatically sets created, updated, createdby, updatedby fields.
    """
    model_name = request.POST.get("model") or request.GET.get("model")
    if not model_name:
        return JsonResponse({"error": "Model name is required"}, status=400)

    Model = get_model_by_name(model_name)
    if not Model:
        return JsonResponse({"error": f"Invalid model name: {model_name}"}, status=400)

    data = []
    # -------------------------
    # 🔹 Parse CSV or JSON
    # -------------------------
    if request.FILES.get("file"):  # CSV upload
        try:
            csv_file = request.FILES["file"]
            file_data = csv_file.read().decode("utf-8").splitlines()
            reader = csv.DictReader(file_data)
            data = list(reader)
        except Exception as e:
            return JsonResponse({"error": f"CSV parsing failed: {str(e)}"}, status=400)
    else:  # JSON upload
        try:
            data = json.loads(request.body.decode("utf-8"))
            if not isinstance(data, list):
                data = [data]
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    if not data:
        return JsonResponse({"error": "No data found in upload"}, status=400)

    objs = []
    now = timezone.now()

    # -------------------------
    # 🔹 Detect user → employee mapping
    # -------------------------
    user = getattr(request, "user", None)
    createdby_instance = None

    if user and user.is_authenticated:
        # Try to resolve correct related model dynamically
        for field in Model._meta.fields:
            if field.name == "createdby":
                related_model = field.related_model
                try:
                    if related_model.__name__.lower() == "user":
                        createdby_instance = user
                    elif related_model.__name__.lower() == "employee":
                        createdby_instance = Employee.objects.filter(user=user).first()
                except Exception as e:
                    print("Error resolving createdby:", e)

    print("👤 Authenticated user:", user)
    print("👥 Resolved createdby_instance:", createdby_instance)

    # -------------------------
    # 🔹 Build model objects
    # -------------------------
    for row in data:
        obj_data = {}
        for field in Model._meta.fields:
            name = field.name
            if name in ["id", "created", "createdby", "updated", "updatedby"]:
                continue
            if name in row and row[name] != "":
                obj_data[name] = row[name]

        obj_data["created"] = now
        obj_data["updated"] = now
        obj_data["createdby"] = createdby_instance
        obj_data["updatedby"] = createdby_instance

        objs.append(Model(**obj_data))

    # -------------------------
    # 🔹 Save all records at once
    # -------------------------
    with transaction.atomic():
        Model.objects.bulk_create(objs, ignore_conflicts=True)

    print(f"✅ Inserted {len(objs)} records into {Model.__name__}")

    return JsonResponse({
        "message": f"✅ Inserted {len(objs)} records into {model_name}",
        "upload_type": "CSV" if request.FILES.get("file") else "JSON"
    })