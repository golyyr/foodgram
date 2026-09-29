from django_filters import rest_framework as filters

from recipes.models import Recipe, Tag


class RecipeFilter(filters.FilterSet):
    """Фильтры списка рецептов: теги, автор, избранное, покупки."""

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_queryset(self, queryset):
        return super().filter_queryset(queryset).distinct()

    def filter_is_favorited(self, queryset, name, value):
        return self._filter_by_user_relation(
            queryset,
            value,
            'favorites__user',
        )

    def filter_is_in_shopping_cart(self, queryset, name, value):
        return self._filter_by_user_relation(
            queryset,
            value,
            'shopping_carts__user',
        )

    def _filter_by_user_relation(self, queryset, value, lookup):
        user = self.request.user
        if not user.is_authenticated:
            if value:
                return queryset.none()
            return queryset
        if value:
            return queryset.filter(**{lookup: user})
        return queryset.exclude(**{lookup: user})
