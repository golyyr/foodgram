from django.db.models import Case, Count, Exists, OuterRef, Sum, When
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import RecipeFilter
from api.pagination import LimitPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeMinifiedSerializer,
    RecipeReadSerializer,
    RecipeUpdateSerializer,
    RecipeWriteSerializer,
    ShortLinkSerializer,
    TagSerializer,
    UserWithRecipesSerializer,
)
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


def redirect_short_link(request, code):
    recipe = get_object_or_404(Recipe, short_code=code)
    return redirect(f'/recipes/{recipe.pk}/')


class UserViewSet(DjoserUserViewSet):
    pagination_class = LimitPagination
    queryset = User.objects.all().order_by('id')

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create', 'reset_password'):
            return [AllowAny()]
        if self.action in (
            'me',
            'avatar',
            'subscriptions',
            'subscribe',
            'set_password',
        ):
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated],
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
            user.avatar = None
            user.save(update_fields=['avatar'])
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(
            user,
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
    )
    def subscriptions(self, request):
        author_ids = list(
            Subscription.objects.filter(user=request.user)
            .order_by('-id')
            .values_list('author_id', flat=True),
        )
        if author_ids:
            order = Case(
                *[
                    When(pk=author_id, then=position)
                    for position, author_id in enumerate(author_ids)
                ],
            )
            authors = User.objects.filter(pk__in=author_ids).annotate(
                recipes_count=Count('recipes'),
            ).order_by(order)
        else:
            authors = User.objects.none()
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        author = self.get_object()
        user = request.user
        if request.method == 'DELETE':
            deleted, _ = Subscription.objects.filter(
                user=user,
                author=author,
            ).delete()
            if not deleted:
                return Response(
                    {'errors': 'Вы не подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)
        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        _, created = Subscription.objects.get_or_create(
            user=user,
            author=author,
        )
        if not created:
            return Response(
                {'errors': 'Вы уже подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = UserWithRecipesSerializer(
            author,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = (AllowAny,)

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = LimitPagination
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags',
            'ingredient_amounts__ingredient',
        )
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=user,
                        recipe=OuterRef('pk'),
                    ),
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user,
                        recipe=OuterRef('pk'),
                    ),
                ),
            )
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeWriteSerializer
        if self.action in ('partial_update', 'update'):
            return RecipeUpdateSerializer
        return RecipeReadSerializer

    def get_permissions(self):
        if self.action in ('partial_update', 'update', 'destroy'):
            return [IsAuthenticated(), IsAuthorOrReadOnly()]
        if self.action in (
            'create',
            'favorite',
            'shopping_cart',
            'download_shopping_cart',
        ):
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        serializer = ShortLinkSerializer(
            recipe,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        return self._toggle_relation(
            request,
            Favorite,
            already_added='Рецепт уже в избранном.',
            missing='Рецепта нет в избранном.',
        )

    @action(detail=True, methods=['post', 'delete'])
    def shopping_cart(self, request, pk=None):
        return self._toggle_relation(
            request,
            ShoppingCart,
            already_added='Рецепт уже в списке покупок.',
            missing='Рецепта нет в списке покупок.',
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        rows = (
            IngredientInRecipe.objects.filter(
                recipe__shopping_carts__user=request.user,
            )
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total=Sum('amount'))
            .order_by('ingredient__name')
        )
        lines = ['Список покупок', '']
        if not rows:
            lines.append('Список пуст.')
        else:
            for row in rows:
                lines.append(
                    '{name} ({unit}) — {total}'.format(
                        name=row['ingredient__name'],
                        unit=row['ingredient__measurement_unit'],
                        total=row['total'],
                    ),
                )
        content = '\n'.join(lines) + '\n'
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping-list.txt"'
        )
        return response

    def _toggle_relation(self, request, model, already_added, missing):
        recipe = self.get_object()
        params = {'user': request.user, 'recipe': recipe}
        if request.method == 'DELETE':
            deleted, _ = model.objects.filter(**params).delete()
            if not deleted:
                return Response(
                    {'errors': missing},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(status=status.HTTP_204_NO_CONTENT)
        if model.objects.filter(**params).exists():
            return Response(
                {'errors': already_added},
                status=status.HTTP_400_BAD_REQUEST,
            )
        model.objects.create(**params)
        serializer = RecipeMinifiedSerializer(
            recipe,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
