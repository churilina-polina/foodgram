import base64

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User

TEST_IMAGE_B64 = (
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD'
    '///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoA'
    'AAAggCByxOyYQAAAABJRU5ErkJggg=='
)

TAGS = (
    ('Завтрак', 'breakfast'),
    ('Обед', 'lunch'),
    ('Ужин', 'dinner'),
)

TEST_USERS = (
    {
        'username': 'vasya.pupkin',
        'email': 'vasya@example.com',
        'first_name': 'Вася',
        'last_name': 'Пупкин',
    },
    {
        'username': 'second_user',
        'email': 'second@example.com',
        'first_name': 'Пётр',
        'last_name': 'Иванов',
    },
    {
        'username': 'third_user',
        'email': 'third@example.com',
        'first_name': 'Мария',
        'last_name': 'Смирнова',
    },
)

TEST_RECIPES = (
    {
        'name': 'Омлет с сыром',
        'text': 'Взбить яйца, добавить сыр, жарить на сковороде 5 минут.',
        'cooking_time': 10,
    },
    {
        'name': 'Овощной суп',
        'text': 'Сварить овощи в бульоне 30 минут, посолить по вкусу.',
        'cooking_time': 40,
    },
    {
        'name': 'Гречка с курицей',
        'text': 'Отварить гречку, обжарить курицу, смешать и потомить.',
        'cooking_time': 35,
    },
)

TEST_USER_PASSWORD = 'foodgram2026'


def make_test_image(name):
    return ContentFile(base64.b64decode(TEST_IMAGE_B64), name=name)


class Command(BaseCommand):
    help = (
        'Создаёт тестовые теги, нескольких пользователей и по одному '
        'рецепту от каждого. Ингредиенты должны быть уже загружены '
        'командой load_ingredients.'
    )

    def handle(self, *args, **options):
        tags = [
            Tag.objects.get_or_create(name=name, slug=slug)[0]
            for name, slug in TAGS
        ]

        ingredients = list(Ingredient.objects.all()[:5])
        if not ingredients:
            self.stdout.write(self.style.WARNING(
                'Ингредиенты не загружены — сначала выполните '
                '`python manage.py load_ingredients`.'
            ))
            return

        for user_data, recipe_data, tag in zip(
            TEST_USERS, TEST_RECIPES, tags,
        ):
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                },
            )
            if created:
                user.set_password(TEST_USER_PASSWORD)
                user.save()

            if Recipe.objects.filter(
                author=user, name=recipe_data['name'],
            ).exists():
                continue

            recipe = Recipe.objects.create(
                author=user,
                name=recipe_data['name'],
                text=recipe_data['text'],
                cooking_time=recipe_data['cooking_time'],
                image=make_test_image(f'{user.username}.png'),
            )
            recipe.tags.add(tag)
            RecipeIngredient.objects.bulk_create(
                RecipeIngredient(
                    recipe=recipe, ingredient=ingredient, amount=100,
                )
                for ingredient in ingredients
            )

        self.stdout.write(self.style.SUCCESS(
            f'Готово: {len(TAGS)} тегов, {len(TEST_USERS)} пользователей '
            f'(пароль для всех: "{TEST_USER_PASSWORD}"), по 1 рецепту.'
        ))
