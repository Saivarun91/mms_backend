from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.postgres.search import TrigramSimilarity
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from matgroups.models import MatGroup
from MaterialType.models import MaterialType
from itemmaster.models import ItemMaster
from .serializers import MatGroupSerializer, MaterialTypeSerializer, ItemMasterSerializer

# 🔹 1. Search Groups by description (with fuzzy match)
@api_view(["POST"])
def search_groups(request):
    query = request.data.get("query", "")
    if not query:
        return Response({"error": "Field 'query' is required"}, status=status.HTTP_400_BAD_REQUEST)

    search_vector = (
        SearchVector("items__item_desc", weight="A") +
        SearchVector("items__search_text", weight="B") +
        SearchVector("notes", weight="A") +
        SearchVector("mgrp_shortname", weight="B") +
        SearchVector("mgrp_longname", weight="B")
    )
    search_query = SearchQuery(query)

    groups = (
        MatGroup.objects.filter(is_deleted=False)
        .annotate(search=search_vector)
        .annotate(rank=SearchRank(search_vector, search_query))
        .annotate(
            trigram_score=(
                TrigramSimilarity("items__item_desc", query) +
                TrigramSimilarity("items__search_text", query) +
                TrigramSimilarity("notes", query) +
                TrigramSimilarity("mgrp_shortname", query) +
                TrigramSimilarity("mgrp_longname", query)
            )
        )
        .filter(rank__gte=0.1)
        .order_by("-trigram_score", "-rank")
        .distinct()
    )

    serializer = MatGroupSerializer(groups, many=True)
    return Response(serializer.data)


# 🔹 2. Get Materials inside a selected group
@api_view(["GET"])
def materials_by_group(request, group_code):
    query = request.GET.get("q", "").strip()
    try:
        group = MatGroup.objects.get(mgrp_code=group_code, is_deleted=False)
    except MatGroup.DoesNotExist:
        return Response({"error": f"MatGroup '{group_code}' not found"}, status=status.HTTP_404_NOT_FOUND)

    materials = MaterialType.objects.filter(
        items__mgrp_code=group,
        is_deleted=False
    ).distinct()

    # (search logic same as you pasted earlier...)

    response_data = []
    for mat in materials:
        response_data.append({
            "mat_type_code": mat.mat_type_code,
            "mat_type_desc": mat.mat_type_desc,
            "sap_id": getattr(mat, "sap_id", None),
            "mgrp_code": group.mgrp_code,
            "mgrp_shortname": group.mgrp_shortname,
            "mgrp_longname": group.mgrp_longname
        })

    return Response(response_data)


@api_view(["GET"])
def sap_ids_by_matgroup(request, group_code):
    try:
        group = MatGroup.objects.get(mgrp_code=group_code, is_deleted=False)
    except MatGroup.DoesNotExist:
        return Response({"message": f"No MatGroup found for '{group_code}'"}, status=404)

    items = ItemMaster.objects.filter(
        mgrp_code=group,
        is_deleted=False
    )

    if not items.exists():
        return Response({"message": f"No items found for material group '{group_code}'"}, status=404)

    response_data = [
        {
            "sap_id": item.sap_item_id,
            "item_desc": item.item_desc,
            "mat_type_code": getattr(item.mat_type_code, "mat_type_code", None),  # use FK field
            "mat_type_desc": getattr(item.mat_type_code, "mat_type_desc", None), 
            "mgrp_code": group.mgrp_code,
            "mgrp_shortname": group.mgrp_shortname,
            "mgrp_longname": group.mgrp_longname
        }
        for item in items
    ]

    return Response(response_data)
# 🔹 3. Get Items inside a selected group
@api_view(["GET"])
def items_by_group(request, group_code):
    query = request.GET.get("q", "")

    items = ItemMaster.objects.filter(
        mgrp_code=group_code,
        is_deleted=False
    )

    if query:
        search_vector = (
            SearchVector("item_desc", weight="A") +
            SearchVector("search_text", weight="B") +
            SearchVector("mat_type_code", weight="B")
        )
        search_query = SearchQuery(query)

        items = (
            items.annotate(search=search_vector)
            .annotate(rank=SearchRank(search_vector, search_query))
            .annotate(
                trigram_score=(
                    TrigramSimilarity("item_desc", query) +
                    TrigramSimilarity("search_text", query) +
                    TrigramSimilarity("mat_type_code", query)
                )
            )
            .filter(rank__gte=0.1)
            .order_by("-trigram_score", "-rank")
        )

    serializer = ItemMasterSerializer(items, many=True)
    return Response(serializer.data)


# 🔹 4. Get Items by group + material type
@api_view(["GET"])
def items_by_group_and_type(request, group_code, mat_type_code):
    query = request.GET.get("q", "")

    items = ItemMaster.objects.filter(
        mgrp_code=group_code,
        mat_type_code=mat_type_code,
        is_deleted=False
    )

    if query:
        search_vector = (
            SearchVector("item_desc", weight="A") +
            SearchVector("search_text", weight="B")
        )
        search_query = SearchQuery(query)

        items = (
            items.annotate(search=search_vector)
            .annotate(rank=SearchRank(search_vector, search_query))
            .annotate(
                trigram_score=(
                    TrigramSimilarity("item_desc", query) +
                    TrigramSimilarity("search_text", query)
                )
            )
            .filter(rank__gte=0.1)
            .order_by("-trigram_score", "-rank")
        )

    serializer = ItemMasterSerializer(items, many=True)
    return Response(serializer.data)



# Hello mic testing mic testing