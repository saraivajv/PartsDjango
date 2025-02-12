import django_filters
from .models import Part

class PartFilter(django_filters.FilterSet):
    part_number = django_filters.CharFilter(field_name="part_number", lookup_expr='icontains')
    name = django_filters.CharFilter(field_name="name", lookup_expr='icontains')
    price = django_filters.NumberFilter(field_name="price", lookup_expr='exact')
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr='lte')

    class Meta:
        model = Part
        fields = ['part_number', 'name', 'price', 'price_min', 'price_max']
