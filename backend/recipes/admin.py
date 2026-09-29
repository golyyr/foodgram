from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe

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

if admin.site.is_registered(Group):
    admin.site.unregister(Group)


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
    related_field = ''

    def lookups(self, request, model_admin):
        return self.lookups_choices

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(
                **{f'{self.related_field}__isnull': False},
            ).distinct()
        if self.value() == 'no':
            return queryset.filter(
                **{f'{self.related_field}__isnull': True},
            )
        return queryset


class HasRecipesFilter(BooleanPresenceFilter):
    title = 'есть в рецептах'
    parameter_name = 'has_recipes'
    lookups_choices = (
        ('yes', 'Есть в рецептах'),
        ('no', 'Нет в рецептах'),
    )
    related_field = 'product_amounts'


class UserHasRecipesFilter(BooleanPresenceFilter):
    title = 'есть рецепты'
    parameter_name = 'has_recipes'
    lookups_choices = (
        ('yes', 'Есть рецепты'),
        ('no', 'Нет рецептов'),
    )
    related_field = 'recipes'


class UserHasSubscriptionsFilter(BooleanPresenceFilter):
    title = 'есть подписки'
    parameter_name = 'has_subscriptions'
    lookups_choices = (
        ('yes', 'Есть подписки'),
        ('no', 'Нет подписок'),
    )
    related_field = 'subscriptions'


class UserHasSubscribersFilter(BooleanPresenceFilter):
    title = 'есть подписчики'
    parameter_name = 'has_subscribers'
    lookups_choices = (
        ('yes', 'Есть подписчики'),
        ('no', 'Нет подписчиков'),
    )
    related_field = 'author_subscriptions'


class CookingTimeFilter(admin.SimpleListFilter):
    title = 'время готовки'
    parameter_name = 'cooking_time_bin'
    ranges = {}

    def lookups(self, request, model_admin):
        times = tuple(
            Recipe.objects.order_by('cooking_time').values_list(
                'cooking_time',
                flat=True,
            ).distinct(),
        )
        count = len(times)
        if count < 3:
            return ()
        first_third = times[count // 3]
        second_third = times[(2 * count) // 3]
        self.ranges = {
            'fast': (times[0], first_third),
            'medium': (first_third, second_third),
            'slow': (second_third, times[-1]),
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
        cooking_range = self.ranges.get(self.value())
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
    def products_list(self, recipe):
        return format_html_join(
            mark_safe('<br>'),
            '{} ({} {})',
            (
                (
                    item.product.name,
                    item.amount,
                    item.product.measurement_unit,
                )
                for item in recipe.product_amounts.select_related('product')
            ),
        )

    @admin.display(description='Теги')
    def tags_list(self, recipe):
        return format_html_join(
            mark_safe('<br>'),
            '{}',
            ((tag.name,) for tag in recipe.tags.all()),
        )

    @admin.display(description='Картинка')
    def image_preview(self, recipe):
        if not recipe.image:
            return ''
        return format_html(
            '<img src="{}" width="80" height="50">',
            recipe.image.url,
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
    filter_horizontal = ()
    readonly_fields = ('date_joined', 'last_login', 'avatar_preview')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Личные данные', {
            'fields': (
                'first_name',
                'last_name',
                'avatar',
                'avatar_preview',
            ),
        }),
        ('Права', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
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
            return '—'
        return format_html(
            '<img src="{}" width="40" height="40" '
            'style="object-fit: cover; border-radius: 50%;">',
            user.avatar.url,
        )
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
