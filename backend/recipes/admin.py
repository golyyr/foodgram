from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe

from recipes.models import (
    Favorite,
    Product,
    ProductInRecipe,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)


class RecipesCountMixin:
    """Показывает число связанных рецептов."""

    @admin.display(description='Рецептов')
    def recipes_count(self, item):
        return item.recipes.count()


class ProductInRecipeInline(admin.TabularInline):
    model = ProductInRecipe
    extra = 1
    min_num = 1


class HasRecipesFilter(admin.SimpleListFilter):
    title = 'есть в рецептах'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Есть в рецептах'),
            ('no', 'Нет в рецептах'),
        )

    def queryset(self, request, products):
        if self.value() == 'yes':
            return products.filter(product_amounts__isnull=False).distinct()
        if self.value() == 'no':
            return products.filter(product_amounts__isnull=True)
        return products


class UserHasRecipesFilter(admin.SimpleListFilter):
    title = 'есть рецепты'
    parameter_name = 'has_recipes'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Есть рецепты'),
            ('no', 'Нет рецептов'),
        )

    def queryset(self, request, users):
        if self.value() == 'yes':
            return users.filter(recipes__isnull=False).distinct()
        if self.value() == 'no':
            return users.filter(recipes__isnull=True)
        return users


class UserHasSubscriptionsFilter(admin.SimpleListFilter):
    title = 'есть подписки'
    parameter_name = 'has_subscriptions'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Есть подписки'),
            ('no', 'Нет подписок'),
        )

    def queryset(self, request, users):
        if self.value() == 'yes':
            return users.filter(subscriptions__isnull=False).distinct()
        if self.value() == 'no':
            return users.filter(subscriptions__isnull=True)
        return users


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'время готовки'
    parameter_name = 'cooking_time_bin'

    def lookups(self, request, model_admin):
        times = list(
            Recipe.objects.order_by('cooking_time').values_list(
                'cooking_time',
                flat=True,
            ),
        )
        if len(times) < 2:
            return ()
        first_third = times[len(times) // 3] if times else 0
        second_third = times[(2 * len(times)) // 3] if times else 0
        if first_third == second_third:
            second_third = first_third + 1
        fast = Recipe.objects.filter(cooking_time__lte=first_third).count()
        medium = Recipe.objects.filter(
            cooking_time__gt=first_third,
            cooking_time__lte=second_third,
        ).count()
        slow = Recipe.objects.filter(cooking_time__gt=second_third).count()
        self._bounds = (first_third, second_third)
        return (
            ('fast', f'быстрее {first_third} мин ({fast})'),
            ('medium', f'быстрее {second_third} мин ({medium})'),
            ('slow', f'долго ({slow})'),
        )

    def queryset(self, request, recipes):
        bounds = getattr(self, '_bounds', None)
        if not bounds:
            times = list(
                Recipe.objects.order_by('cooking_time').values_list(
                    'cooking_time',
                    flat=True,
                ),
            )
            if len(times) < 2:
                return recipes
            first_third = times[len(times) // 3]
            second_third = times[(2 * len(times)) // 3]
            if first_third == second_third:
                second_third = first_third + 1
            bounds = (first_third, second_third)
        first_third, second_third = bounds
        if self.value() == 'fast':
            return recipes.filter(cooking_time__lte=first_third)
        if self.value() == 'medium':
            return recipes.filter(
                cooking_time__gt=first_third,
                cooking_time__lte=second_third,
            )
        if self.value() == 'slow':
            return recipes.filter(cooking_time__gt=second_third)
        return recipes


@admin.register(Tag)
class TagAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'recipes_count')
    search_fields = ('name', 'slug')


@admin.register(Product)
class ProductAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit', 'recipes_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = (HasRecipesFilter, 'measurement_unit')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'cooking_time',
        'author_name',
        'favorites_count',
        'products_list',
        'tags_list',
        'image_preview',
    )
    search_fields = (
        'name',
        'author__username',
        'author__email',
        'author__first_name',
        'author__last_name',
        'tags__name',
        'products__name',
    )
    list_filter = ('tags', 'author', CookingTimeFilter)
    readonly_fields = ('favorites_count', 'pub_date')
    inlines = (ProductInRecipeInline,)
    filter_horizontal = ('tags',)
    fieldsets = (
        ('Статистика', {'fields': ('favorites_count',)}),
        (None, {
            'fields': (
                'author',
                'name',
                'image',
                'text',
                'cooking_time',
                'tags',
                'pub_date',
            ),
        }),
    )

    @admin.display(description='Автор')
    def author_name(self, recipe):
        return recipe.author.get_full_name()

    @admin.display(description='В избранном')
    def favorites_count(self, recipe):
        return recipe.favorites.count()

    @admin.display(description='Продукты')
    def products_list(self, recipe):
        return mark_safe('<br>'.join(
            f'{item.product.name} ({item.amount} '
            f'{item.product.measurement_unit})'
            for item in recipe.product_amounts.select_related('product')
        ))

    @admin.display(description='Теги')
    def tags_list(self, recipe):
        return ', '.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Картинка')
    def image_preview(self, recipe):
        if not recipe.image:
            return ''
        return mark_safe(
            f'<img src="{recipe.image.url}" width="80" height="50">',
        )


@admin.register(ProductInRecipe)
class ProductInRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'product', 'amount')
    search_fields = ('recipe__name', 'product__name')


@admin.register(Favorite, ShoppingCart)
class UserRecipeRelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'avatar_preview',
        'recipes_count',
        'subscriptions_count',
        'subscribers_count',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
        UserHasRecipesFilter,
        UserHasSubscriptionsFilter,
    )
    ordering = ('username',)
    readonly_fields = ('date_joined', 'last_login')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Личные данные', {
            'fields': ('first_name', 'last_name', 'avatar'),
        }),
        ('Права', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
        }),
        ('Даты', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'first_name',
                'last_name',
                'password1',
                'password2',
            ),
        }),
    )

    @admin.display(description='ФИО')
    def full_name(self, user):
        return user.get_full_name()

    @admin.display(description='Аватар')
    def avatar_preview(self, user):
        if not user.avatar:
            return ''
        return mark_safe(
            f'<img src="{user.avatar.url}" width="40" height="40">',
        )

    @admin.display(description='Рецептов')
    def recipes_count(self, user):
        return user.recipes.count()

    @admin.display(description='Подписок')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчиков')
    def subscribers_count(self, user):
        return user.subscribers.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author')
    search_fields = (
        'user__username',
        'user__email',
        'author__username',
        'author__email',
    )
    list_filter = ('author',)
