from django.db.models import BooleanField, Exists, OuterRef, Value
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    SAFE_METHODS, AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Subscribe, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import PageLimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer, IngredientSerializer, RecipeMinifiedSerializer,
    RecipeReadSerializer, RecipeWriteSerializer, TagSerializer,
    UserWithRecipesSerializer,
)
from .utils import build_shopping_cart_content


class CustomUserViewSet(DjoserUserViewSet):
    pagination_class = PageLimitPagination

    def get_permissions(self):
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(
        detail=False,
        methods=('put', 'delete'),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(
            user, data=request.data, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        authors = User.objects.filter(
            subscribers__user=request.user,
        ).order_by('-subscribers__id')
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={'request': request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        user = request.user

        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            _, created = Subscribe.objects.get_or_create(
                user=user, author=author,
            )
            if not created:
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = UserWithRecipesSerializer(
                author, context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Subscribe.objects.filter(
            user=user, author=author,
        ).delete()
        if not deleted:
            return Response(
                {'errors': 'Вы не были подписаны на этого автора.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


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
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    pagination_class = PageLimitPagination
    filterset_class = RecipeFilter

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags', 'recipe_ingredients__ingredient',
        )
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=user, recipe=OuterRef('pk'),
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=user, recipe=OuterRef('pk'),
                    )
                ),
            )
        else:
            queryset = queryset.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField()),
            )
        return queryset

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _handle_relation(self, request, pk, model, add_error, remove_error):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            _, created = model.objects.get_or_create(user=user, recipe=recipe)
            if not created:
                return Response(
                    {'errors': add_error}, status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = RecipeMinifiedSerializer(
                recipe, context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = model.objects.filter(user=user, recipe=recipe).delete()
        if not deleted:
            return Response(
                {'errors': remove_error}, status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True, methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        return self._handle_relation(
            request, pk, Favorite,
            'Рецепт уже добавлен в избранное.',
            'Этого рецепта не было в избранном.',
        )

    @action(
        detail=True, methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        return self._handle_relation(
            request, pk, ShoppingCart,
            'Рецепт уже добавлен в список покупок.',
            'Этого рецепта не было в списке покупок.',
        )

    @action(
        detail=False, methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        content = build_shopping_cart_content(request.user)
        response = HttpResponse(
            content, content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=True, methods=('get',), url_path='get-link')
    def get_link(self, request, pk=None):
        get_object_or_404(Recipe, pk=pk)
        short_link = request.build_absolute_uri(f'/s/{pk}/')
        return Response({'short-link': short_link})
