from functools import wraps

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Max, Min
from django.utils.safestring import mark_safe as mark_safe_value

from .models import (
    Favorite,
    Product,
    ProductInRecipe,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
    User,
)


def mark_safe(method):
    """Декоратор: помечает HTML-результат метода как безопасный."""

    @wraps(method)
    def wrapper(*args, **kwargs):
        return mark_safe_value(method(*args, **kwargs))

    return wrapper


class RecipesCountMixin:
    """Добавляет столбец с числом связанных рецептов."""

    list_display = ('recipes_count',)

    @admin.display(description='Рецептов')
    def recipes_count(self, item):
        return item.recipes.count()


class ProductInRecipeInline(admin.TabularInline):
    model = ProductInRecipe
    extra = 1
    min_num = 1


class BooleanPresenceFilter(admin.SimpleListFilter):
    """Базовый фильтр наличия связанных объектов."""

    title = ''
    parameter_name = ''
    lookups_choices = ()
    yes_filter = {}
    no_filter = {}

    def lookups(self, request, model_admin):
        return self.lookups_choices

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(**self.yes_filter).distinct()
        if self.value() == 'no':
            return queryset.filter(**self.no_filter)
        return queryset


class HasRecipesFilter(BooleanPresenceFilter):
    title = 'есть в рецептах'
    parameter_name = 'has_recipes'
    lookups_choices = (
        ('yes', 'Есть в рецептах'),
        ('no', 'Нет в рецептах'),
    )
    yes_filter = {'product_amounts__isnull': False}
    no_filter = {'product_amounts__isnull': True}


class UserHasRecipesFilter(BooleanPresenceFilter):
    title = 'есть рецепты'
    parameter_name = 'has_recipes'
    lookups_choices = (
        ('yes', 'Есть рецепты'),
        ('no', 'Нет рецептов'),
    )
    yes_filter = {'recipes__isnull': False}
    no_filter = {'recipes__isnull': True}


class UserHasSubscriptionsFilter(BooleanPresenceFilter):
    title = 'есть подписки'
    parameter_name = 'has_subscriptions'
    lookups_choices = (
        ('yes', 'Есть подписки'),
        ('no', 'Нет подписок'),
    )
    yes_filter = {'subscriptions__isnull': False}
    no_filter = {'subscriptions__isnull': True}


class UserHasSubscribersFilter(BooleanPresenceFilter):
    title = 'есть подписчики'
    parameter_name = 'has_subscribers'
    lookups_choices = (
        ('yes', 'Есть подписчики'),
        ('no', 'Нет подписчиков'),
    )
    yes_filter = {'author_subscriptions__isnull': False}
    no_filter = {'author_subscriptions__isnull': True}


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'время готовки'
    parameter_name = 'cooking_time_bin'

    def lookups(self, request, model_admin):
        times = Recipe.objects.order_by('cooking_time').values_list(
            'cooking_time',
            flat=True,
        ).distinct()
        count = times.count()
        if count < 3:
            return ()
        first_third = times[count // 3]
        second_third = times[(2 * count) // 3]
        max_time = Recipe.objects.aggregate(value=Max('cooking_time'))['value']
        min_time = Recipe.objects.aggregate(value=Min('cooking_time'))['value']
        self.ranges = {
            'fast': (min_time, first_third),
            'medium': (first_third, second_third),
            'slow': (second_third, max_time),
        }
        return (
            (
                'fast',
                'быстрее {bound} мин ({count})'.format(
                    bound=first_third,
                    count=Recipe.objects.filter(
                        cooking_time__range=self.ranges['fast'],
                    ).count(),
                ),
            ),
            (
                'medium',
                'быстрее {bound} мин ({count})'.format(
                    bound=second_third,
                    count=Recipe.objects.filter(
                        cooking_time__range=self.ranges['medium'],
                    ).count(),
                ),
            ),
            (
                'slow',
                'долго ({count})'.format(
                    count=Recipe.objects.filter(
                        cooking_time__range=self.ranges['slow'],
                    ).count(),
                ),
            ),
        )

    def queryset(self, request, recipes):
        cooking_range = getattr(self, 'ranges', {}).get(self.value())
        if cooking_range is None:
            return recipes
        return recipes.filter(cooking_time__range=cooking_range)


@admin.register(Tag)
class TagAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', *RecipesCountMixin.list_display)
    search_fields = ('name', 'slug')


@admin.register(Product)
class ProductAdmin(RecipesCountMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit',
        *RecipesCountMixin.list_display,
    )
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
    @mark_safe
    def products_list(self, recipe):
        return '<br>'.join(
            f'{item.product.name} ({item.amount} '
            f'{item.product.measurement_unit})'
            for item in recipe.product_amounts.select_related('product')
        )

    @admin.display(description='Теги')
    @mark_safe
    def tags_list(self, recipe):
        return '<br>'.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Картинка')
    @mark_safe
    def image_preview(self, recipe):
        if not recipe.image:
            return ''
        return f'<img src="{recipe.image.url}" width="80" height="50">'


@admin.register(ProductInRecipe)
class ProductInRecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'product', 'amount')
    search_fields = ('recipe__name', 'product__name')


@admin.register(Favorite, ShoppingCart)
class UserRecipeRelationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    search_fields = ('user__username', 'user__email', 'recipe__name')


@admin.register(User)
class UserAdmin(RecipesCountMixin, BaseUserAdmin):
    list_display = (
        'id',
        'username',
        'full_name',
        'email',
        'avatar_preview',
        *RecipesCountMixin.list_display,
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
        UserHasSubscribersFilter,
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
    @mark_safe
    def avatar_preview(self, user):
        if not user.avatar:
            return ''
        return f'<img src="{user.avatar.url}" width="40" height="40">'

    @admin.display(description='Подписок')
    def subscriptions_count(self, user):
        return user.subscriptions.count()

    @admin.display(description='Подписчиков')
    def subscribers_count(self, user):
        return user.author_subscriptions.count()


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
