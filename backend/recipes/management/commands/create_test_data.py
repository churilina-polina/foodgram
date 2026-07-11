import io

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User

PLACEHOLDER_COLORS = (
    (255, 179, 71),
    (108, 178, 108),
    (94, 139, 209),
    (219, 112, 147),
    (147, 112, 219),
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
        'author': 'vasya.pupkin',
        'tags': ('breakfast',),
    },
    {
        'name': 'Сырники со сметаной',
        'text': (
            'Смешать творог, яйцо и муку, обжарить сырники до румяной '
            'корочки, подавать со сметаной.'
        ),
        'cooking_time': 20,
        'author': 'vasya.pupkin',
        'tags': ('breakfast',),
    },
    {
        'name': 'Блины на кефире',
        'text': (
            'Замесить тесто на кефире, выпекать блины на раскалённой '
            'сковороде с двух сторон.'
        ),
        'cooking_time': 25,
        'author': 'vasya.pupkin',
        'tags': ('breakfast',),
    },
    {
        'name': 'Овощной суп',
        'text': 'Сварить овощи в бульоне 30 минут, посолить по вкусу.',
        'cooking_time': 40,
        'author': 'second_user',
        'tags': ('lunch',),
    },
    {
        'name': 'Салат Цезарь с курицей',
        'text': (
            'Обжарить курицу и сухарики, смешать с листьями салата и '
            'соусом цезарь, посыпать пармезаном.'
        ),
        'cooking_time': 15,
        'author': 'second_user',
        'tags': ('lunch', 'dinner'),
    },
    {
        'name': 'Куриный бульон с лапшой',
        'text': (
            'Сварить бульон из курицы, добавить лапшу и зелень, '
            'проварить ещё 10 минут.'
        ),
        'cooking_time': 45,
        'author': 'second_user',
        'tags': ('lunch',),
    },
    {
        'name': 'Гречка с курицей',
        'text': 'Отварить гречку, обжарить курицу, смешать и потомить.',
        'cooking_time': 35,
        'author': 'third_user',
        'tags': ('lunch', 'dinner'),
    },
    {
        'name': 'Плов с курицей',
        'text': (
            'Обжарить курицу с морковью и луком, добавить рис и воду, '
            'томить под крышкой до готовности риса.'
        ),
        'cooking_time': 50,
        'author': 'third_user',
        'tags': ('lunch', 'dinner'),
    },
)

TEST_USER_PASSWORD = 'foodgram2026'


def make_test_image(name, label, color):
    image = Image.new('RGB', (600, 400), color=color)
    draw = ImageDraw.Draw(image)
    words = label.split()
    lines, current = [], ''
    for word in words:
        candidate = f'{current} {word}'.strip()
        if len(candidate) > 16:
            lines.append(current)
            current = word
        else:
            current = candidate
    lines.append(current)
    line_height = 28
    start_y = 200 - (len(lines) * line_height) // 2
    for i, line in enumerate(lines):
        draw.text(
            (40, start_y + i * line_height), line, fill=(255, 255, 255),
        )
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return ContentFile(buffer.getvalue(), name=name)


class Command(BaseCommand):
    help = (
        'Создаёт тестовые теги, нескольких пользователей и несколько '
        'рецептов от каждого. Ингредиенты должны быть уже загружены '
        'командой load_ingredients.'
    )

    def handle(self, *args, **options):
        tags_by_slug = {
            slug: Tag.objects.get_or_create(name=name, slug=slug)[0]
            for name, slug in TAGS
        }

        ingredients = list(Ingredient.objects.all()[:5])
        if not ingredients:
            self.stdout.write(self.style.WARNING(
                'Ингредиенты не загружены — сначала выполните '
                '`python manage.py load_ingredients`.'
            ))
            return

        users_by_username = {}
        for user_data in TEST_USERS:
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
            users_by_username[user_data['username']] = user

        created_count = 0
        for index, recipe_data in enumerate(TEST_RECIPES):
            author = users_by_username[recipe_data['author']]
            if Recipe.objects.filter(
                author=author, name=recipe_data['name'],
            ).exists():
                continue

            recipe = Recipe.objects.create(
                author=author,
                name=recipe_data['name'],
                text=recipe_data['text'],
                cooking_time=recipe_data['cooking_time'],
                image=make_test_image(
                    f'{author.username}-{index}.png',
                    recipe_data['name'],
                    PLACEHOLDER_COLORS[index % len(PLACEHOLDER_COLORS)],
                ),
            )
            recipe.tags.set(
                tags_by_slug[slug] for slug in recipe_data['tags']
            )
            RecipeIngredient.objects.bulk_create(
                RecipeIngredient(
                    recipe=recipe, ingredient=ingredient, amount=100,
                )
                for ingredient in ingredients
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Готово: {len(TAGS)} тегов, {len(TEST_USERS)} пользователей '
            f'(пароль для всех: "{TEST_USER_PASSWORD}"), '
            f'создано новых рецептов: {created_count}.'
        ))
