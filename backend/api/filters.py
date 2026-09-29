from django_filters import rest_framework as filters

from recipes.models import Product, Recipe, Tag


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

    def filter_queryset(self, recipes):
        return super().filter_queryset(recipes).distinct()

    def filter_is_favorited(self, recipes, name, value):
        return self._filter_by_user_relation(
            recipes,
            value,
            'favorites__user',
        )

    def filter_is_in_shopping_cart(self, recipes, name, value):
        return self._filter_by_user_relation(
            recipes,
            value,
            'shoppingcarts__user',
        )

    def _filter_by_user_relation(self, recipes, value, lookup):
        current_user = self.request.user
        if not current_user.is_authenticated:
            if value:
                return recipes.none()
            return recipes
        if value:
            return recipes.filter(**{lookup: current_user})
        return recipes.exclude(**{lookup: current_user})


class ProductFilter(filters.FilterSet):
    """Поиск продуктов по началу названия."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Product
        fields = ('name',)
