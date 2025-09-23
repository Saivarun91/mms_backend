from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.contrib.postgres.search import TrigramSimilarity
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from matgroups.models import MatGroup
from MaterialType.models import MaterialType
from itemmaster.models import ItemMaster
from .serializers import MatGroupSerializer, MaterialTypeSerializer, ItemMasterSerializer


# 🔹 1. Search Groups by description (Hybrid BM25 + Trigram)
@api_view(["POST"])
def search_groups(request):
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

    # BM25 results
    bm25_qs = (
        MatGroup.objects.filter(is_deleted=False)
        .annotate(search=search_vector)
        .annotate(rank=SearchRank(search_vector, search_query))
        .filter(rank__gte=0.1)
    )

    # Trigram results
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

    # Merge both
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

    # (Optional: could add BM25 + trigram for searching materials if needed)

    response_data = [
        {
            "mat_type_code": mat.mat_type_code,
            "mat_type_desc": mat.mat_type_desc,
            "sap_id": getattr(mat, "sap_id", None),
            "mgrp_code": group.mgrp_code,
            "mgrp_shortname": group.mgrp_shortname,
            "mgrp_longname": group.mgrp_longname,
        }
        for mat in materials
    ]

    return Response(response_data)


# 🔹 3. Get Items inside a selected group (Hybrid BM25 + Trigram)
@api_view(["GET"])
def items_by_group(request, group_code):
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


# 🔹 4. Get Items by group + material type (Hybrid BM25 + Trigram)
@api_view(["GET"])
def items_by_group_and_type(request, group_code, mat_type_code):
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


# 🔹 5. Get SAP IDs inside a selected group
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
            "mat_type_code": getattr(item.mat_type_code, "mat_type_code", None),
            "mat_type_desc": getattr(item.mat_type_code, "mat_type_desc", None),
            "mgrp_code": group.mgrp_code,
            "mgrp_shortname": group.mgrp_shortname,
            "mgrp_longname": group.mgrp_longname,
        }
        for item in items
    ]

    return Response(response_data)
