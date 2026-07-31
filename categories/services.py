'''Category creation services.'''

from .models import Category


DEFAULT_CATEGORIES = (
    {
        'name': 'Estudos',
        'slug': 'estudos',
        'color_token': Category.ColorToken.BRAND,
    },
    {
        'name': 'Trabalho',
        'slug': 'trabalho',
        'color_token': Category.ColorToken.CYAN,
    },
    {
        'name': 'Pessoal',
        'slug': 'pessoal',
        'color_token': Category.ColorToken.SUCCESS,
    },
    {
        'name': 'Saúde',
        'slug': 'saude',
        'color_token': Category.ColorToken.DANGER,
    },
)


def create_default_categories(*, workspace):
    '''Create the standard categories without duplicating existing records.'''

    categories = []
    for category_data in DEFAULT_CATEGORIES:
        category, _created = Category.objects.get_or_create(
            workspace=workspace,
            slug=category_data['slug'],
            defaults={
                'name': category_data['name'],
                'color_token': category_data['color_token'],
                'is_system': True,
            },
        )
        categories.append(category)
    return categories
