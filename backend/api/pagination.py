from rest_framework.pagination import PageNumberPagination

from .constants import MAX_PAGE_SIZE, PAGE_SIZE


class LimitPagination(PageNumberPagination):
    """Пагинация с параметром limit, как его ждёт фронтенд."""

    page_size = PAGE_SIZE
    page_size_query_param = 'limit'
    max_page_size = MAX_PAGE_SIZE
