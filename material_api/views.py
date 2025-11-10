from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from matgroups.models import MatGroup
from MaterialType.models import MaterialType
from itemmaster.models import ItemMaster
from .serializers import MatGroupSerializer, MaterialTypeSerializer, ItemMasterSerializer


# ==============================================================
# 🔹 1. Free Text Search (Hybrid BM25 + Trigram)
# ==============================================================
@api_view(["POST"])
def search_groups(request):
    """
    Free-text hybrid search across Material Groups using BM25 + Trigram.
    """
    query = request.data.get("query", "").strip()
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

    # BM25 relevance
    bm25_qs = (
        MatGroup.objects.filter(is_deleted=False)
        .annotate(search=search_vector)
        .annotate(rank=SearchRank(search_vector, search_query))
        .filter(rank__gte=0.1)
    )

    # Trigram fuzzy search
    trigram_qs = (
        MatGroup.objects.filter(is_deleted=False)
        .annotate(
            trigram_score=(
                TrigramSimilarity("items__item_desc", query) +
                TrigramSimilarity("items__search_text", query) +
                TrigramSimilarity("notes", query) +
                TrigramSimilarity("mgrp_shortname", query) +
                TrigramSimilarity("mgrp_longname", query)
            )
        )
        .filter(trigram_score__gte=0.2)
    )

    # Merge both results
    groups = (bm25_qs | trigram_qs).annotate(
        rank=SearchRank(search_vector, search_query),
        score=(
            TrigramSimilarity("items__item_desc", query) +
            TrigramSimilarity("items__search_text", query) +
            TrigramSimilarity("notes", query) +
            TrigramSimilarity("mgrp_shortname", query) +
            TrigramSimilarity("mgrp_longname", query)
        )
    ).order_by("-rank", "-score").distinct()

    def truncate(num, digits=2):
        factor = 10.0 ** digits
        return int(num * factor) / factor

    data = [
        {**MatGroupSerializer(group).data, "score": group.score, "rank": truncate(group.rank * 100, 2)}
        for group in groups
    ]
    return Response(data)


# ==============================================================
# 🔹 2. Drill-Down Search APIs
# ==============================================================
# This section enables manual navigation:
# Super Material Group → Material Group → Material → Items
# ==============================================================

@api_view(["GET"])
def super_material_groups(request):
    """
    Get all top-level (super) material groups.
    Assumes hierarchy via parent_group FK in MatGroup.
    """
    super_groups = MatGroup.objects.filter(is_deleted=False, parent_group__isnull=True)
    data = [
        {
            "super_code": grp.mgrp_code,
            "super_name": grp.mgrp_longname,
            "short_name": grp.mgrp_shortname,
        }
        for grp in super_groups
    ]
    return Response(data)


@api_view(["GET"])
def material_groups_by_super(request, super_code):
    """
    Get all material groups under a selected super group.
    """
    groups = MatGroup.objects.filter(
        parent_group__mgrp_code=super_code,
        is_deleted=False
    )
    if not groups.exists():
        return Response({"message": "No material groups found for this super group"}, status=404)

    data = [
        {
            "mgrp_code": g.mgrp_code,
            "mgrp_shortname": g.mgrp_shortname,
            "mgrp_longname": g.mgrp_longname,
        }
        for g in groups
    ]
    return Response(data)


@api_view(["GET"])
def materials_by_matgroup(request, mgrp_code):
    """
    Get all material types under a specific material group.
    """
    materials = MaterialType.objects.filter(
        items__mgrp_code=mgrp_code,
        is_deleted=False
    ).distinct()

    data = [
        {
            "mat_type_code": m.mat_type_code,
            "mat_type_desc": m.mat_type_desc,
        }
        for m in materials
    ]
    return Response(data)


@api_view(["GET"])
def items_by_material_type(request, mat_type_code):
    """
    Get all items under a specific material type.
    """
    items = ItemMaster.objects.filter(
        mat_type_code=mat_type_code,
        is_deleted=False
    )

    data = [
        {
            "sap_id": i.sap_item_id,
            "item_desc": i.item_desc,
            "mgrp_code": i.mgrp_code.mgrp_code if i.mgrp_code else None,
            "mat_type_code": mat_type_code,
        }
        for i in items
    ]
    return Response(data)


# ==============================================================
# 🔹 3. Search by Material Group Code (Direct Lookup)
# ==============================================================
@api_view(["GET"])
def search_by_matgroup_code(request, mgrp_code):
    """
    Search directly by a known Material Group code.
    Returns the group, its materials, and items.
    """
    try:
        group = MatGroup.objects.get(mgrp_code=mgrp_code, is_deleted=False)
    except MatGroup.DoesNotExist:
        return Response({"error": "Invalid Material Group Code"}, status=404)

    # Materials in this group
    materials = MaterialType.objects.filter(
        items__mgrp_code=group,
        is_deleted=False
    ).distinct()

    # Items in this group
    items = ItemMaster.objects.filter(
        mgrp_code=group,
        is_deleted=False
    )

    data = {
        "group": {
            "mgrp_code": group.mgrp_code,
            "mgrp_shortname": group.mgrp_shortname,
            "mgrp_longname": group.mgrp_longname,
        },
        "materials": [
            {
                "mat_type_code": m.mat_type_code,
                "mat_type_desc": m.mat_type_desc,
            }
            for m in materials
        ],
        "items": [
            {
                "sap_id": i.sap_item_id,
                "item_desc": i.item_desc,
            }
            for i in items
        ]
    }
    return Response(data)


# ==============================================================
# 🔹 4. Items by Group (with optional text filter)
# ==============================================================
@api_view(["GET"])
def items_by_group(request, group_code):
    """
    Get items under a group, optionally filtered with text query.
    """
    query = request.GET.get("q", "").strip()

    items = ItemMaster.objects.filter(
        mgrp_code=group_code,
        is_deleted=False
    )

    if query:
        search_vector = (
            SearchVector("item_desc", weight="A") +
            SearchVector("search_text", weight="B") +
            SearchVector("mat_type_code", weight="C")
        )
        search_query = SearchQuery(query)

        bm25_qs = (
            items.annotate(search=search_vector)
            .annotate(rank=SearchRank(search_vector, search_query))
            .filter(rank__gte=0.1)
        )

        trigram_qs = (
            items.annotate(
                trigram_score=(
                    TrigramSimilarity("item_desc", query) +
                    TrigramSimilarity("search_text", query) +
                    TrigramSimilarity("mat_type_code", query)
                )
            ).filter(trigram_score__gte=0.2)
        )

        items = (bm25_qs | trigram_qs).annotate(
            rank=SearchRank(search_vector, search_query),
            trigram_score=(
                TrigramSimilarity("item_desc", query) +
                TrigramSimilarity("search_text", query) +
                TrigramSimilarity("mat_type_code", query)
            )
        ).order_by("-rank", "-trigram_score").distinct()

    serializer = ItemMasterSerializer(items, many=True)
    return Response(serializer.data)


# ==============================================================
# 🔹 5. Items by Group + Material Type (Hybrid Search)
# ==============================================================
@api_view(["GET"])
def items_by_group_and_type(request, group_code, mat_type_code):
    """
    Get items by group + material type, optionally with text search.
    """
    query = request.GET.get("q", "").strip()

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

        bm25_qs = (
            items.annotate(search=search_vector)
            .annotate(rank=SearchRank(search_vector, search_query))
            .filter(rank__gte=0.1)
        )

        trigram_qs = (
            items.annotate(
                trigram_score=(
                    TrigramSimilarity("item_desc", query) +
                    TrigramSimilarity("search_text", query)
                )
            ).filter(trigram_score__gte=0.2)
        )

        items = (bm25_qs | trigram_qs).annotate(
            rank=SearchRank(search_vector, search_query),
            trigram_score=(
                TrigramSimilarity("item_desc", query) +
                TrigramSimilarity("search_text", query)
            )
        ).order_by("-rank", "-trigram_score").distinct()

    serializer = ItemMasterSerializer(items, many=True)
    return Response(serializer.data)


# ==============================================================
# 🔹 6. SAP IDs by Material Group
# ==============================================================
@api_view(["GET"])
def sap_ids_by_matgroup(request, group_code):
    """
    Get all SAP IDs and related info for a selected material group.
    """
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
            "mat_type_code": getattr(item.mat_type_code, "mat_type_code", None),
            "mat_type_desc": getattr(item.mat_type_code, "mat_type_desc", None),
            "mgrp_code": group.mgrp_code,
            "mgrp_shortname": group.mgrp_shortname,
            "mgrp_longname": group.mgrp_longname,
        }
        for item in items
    ]

    return Response(response_data)
