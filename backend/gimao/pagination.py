from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class BasePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class StandardPagination(BasePagination):
    page_size = 10


class LargePagination(BasePagination):
    page_size = 25


class PaginatedActionMixin:
    """
    Mutualise la pagination des actions custom pour conserver le même
    contrat DRF (`count`, `next`, `previous`, `results`) que sur `list`.
    """

    def get_paginated_response_for_queryset(
        self,
        queryset,
        *,
        serializer_class=None,
        extra=None,
        many=True,
    ):
        page = self.paginate_queryset(queryset)

        if serializer_class is None:

            def serializer_factory(items):
                return self.get_serializer(items, many=many)
        else:

            def serializer_factory(items):
                return serializer_class(
                    items,
                    many=many,
                    context=self.get_serializer_context(),
                )

        serializer = serializer_factory(page if page is not None else queryset)

        if not extra:
            return self.get_paginated_response(serializer.data)

        return Response(
            {
                "count": self.paginator.page.paginator.count,
                "next": self.paginator.get_next_link(),
                "previous": self.paginator.get_previous_link(),
                "results": serializer.data,
                **extra,
            }
        )
