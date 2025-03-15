import abc
import calendar
import datetime
from datetime import date
from enum import IntEnum
from typing import Literal

from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class DateLimit(IntEnum):
    LEFT = -1
    RIGHT = 1
    BOTH = 0


class FilterFactory(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def new(cls, *args, **kwargs) -> admin.SimpleListFilter:
        ...


class YearLimitFilterFactory(FilterFactory):

    @classmethod
    def new(cls, field_name='created', filter_type: Literal['before', 'after', 'since', 'until'] = 'after'):
        class YearLimitListFilter(admin.SimpleListFilter):
            title = f'{field_name.title()} {filter_type.title()}'
            parameter_name = f'{field_name}_{filter_type}'
            lookup_opr = {
                'since': '__gte',
                'until': '__lte',
                'before': '__lt',
                'after': '__gt'
            }.get(filter_type)

            def __init__(self, request, new_params, model, *args, **kwargs):
                self.model = model
                super().__init__(request, new_params, model, *args, **kwargs)

            def lookups(self, request, model_admin):
                qs = self.model.objects.filter()
                value_field = f'{field_name}__year'
                choices = qs.values_list(value_field, flat=True).order_by(value_field).distinct()
                return ((yr, f'{yr}') for yr in choices)

            def queryset(self, request, queryset):
                try:
                    value = int(self.value())
                    if filter_type == 'after':
                        flt = {f'{field_name}__year{self.lookup_opr}': value}
                    else:
                        flt = {f'{field_name}__year{self.lookup_opr}': value}
                except (ValueError, TypeError):
                    flt = {}
                return queryset.filter(**flt)

        return YearLimitListFilter


class YearFilterFactory(FilterFactory):

    @classmethod
    def new(cls, field_name='created', reverse=True):

        class YearFilter(admin.SimpleListFilter):
            parameter_name = f'{field_name}_year'
            title = parameter_name.replace('_', ' ').title()

            def __init__(self, request, new_params, model, *args, **kwargs):
                self.model = model
                super().__init__(request, new_params, model, *args, **kwargs)

            def lookups(self, request, model_admin):
                qs = self.model.objects.filter()
                value_field = f'{field_name}__year'
                order_field = value_field if not reverse else f'-{value_field}'
                choices = qs.values_list(value_field, flat=True).order_by(order_field).distinct()
                return ((yr, f'{yr}') for yr in choices)

            def queryset(self, request, queryset):
                flt = {} if not self.value() else {f'{field_name}__year': self.value()}
                return queryset.filter(**flt)

        return YearFilter


class MonthFilterFactory(FilterFactory):
    @classmethod
    def new(cls, field_name='created'):
        class MonthFilter(admin.SimpleListFilter):
            parameter_name = f'{field_name}_month'
            title = parameter_name.replace('_', ' ').title()

            def __init__(self, request, new_params, model, *args, **kwargs):
                self.model = model
                super().__init__(request, new_params, model, *args, **kwargs)

            def lookups(self, request, model_admin):
                return ((month, calendar.month_name[month]) for month in range(1, 13))

            def queryset(self, request, queryset):
                flt = {} if not self.value() else {f'{field_name}__month': self.value()}
                return queryset.filter(**flt)

        return MonthFilter


class QuarterFilterFactory(FilterFactory):
    @classmethod
    def new(cls, field_name='created'):
        class QuarterFilter(admin.SimpleListFilter):
            parameter_name = f'{field_name}_quarter'
            title = parameter_name.replace('_', ' ').title()

            def __init__(self, request, new_params, model, *args, **kwargs):
                self.model = model
                super().__init__(request, new_params, model, *args, **kwargs)

            def lookups(self, request, model_admin):
                return ((i + 1, f'Q{i + 1}') for i in range(4))

            def queryset(self, request, queryset):
                flt = {} if not self.value() else {f'{field_name}__quarter': self.value()}
                return queryset.filter(**flt)

        return QuarterFilter


class ExpiryDateListFilterFactory(FilterFactory):
    @classmethod
    def new(cls, field_name='due_date'):
        class ExpiryDateListFilter(admin.SimpleListFilter):
            parameter_name = f'{field_name}_expiry'
            title = field_name.title().replace('_', ' ')

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

            def lookups(self, request, model_admin):
                return [
                    ('expired', _('Expired')), ('today', _('Today')), ('tomorrow', _('Tomorrow')),
                    ('7days', _('Within 7 days')), ('month', _('This month')), ('year', _('This year')),
                ]

            def queryset(self, request, queryset):
                now = timezone.now()
                # When time zone support is enabled, convert "now" to the user's time
                # zone so Django's definition of "Today" matches what the user expects.
                if timezone.is_aware(now):
                    now = timezone.localtime(now)

                today = now.date()
                tomorrow = today + datetime.timedelta(days=1)
                if today.month == 12:
                    next_month = today.replace(year=today.year + 1, month=1, day=1)
                else:
                    next_month = today.replace(month=today.month + 1, day=1)
                next_year = today.replace(year=today.year + 1, month=1, day=1)

                kwarg_since = f'{field_name}__gte'
                kwarg_until = f'{field_name}__lt'

                if not self.value():
                    query = {}
                elif self.value() == 'expired':
                    query = {kwarg_until: today}
                elif self.value() == 'today':
                    query = {field_name: tomorrow}
                elif self.value() == 'tomorrow':
                    query = {field_name: today}
                elif self.value() == '7days':
                    query = {kwarg_since: today, kwarg_until: today + datetime.timedelta(days=7)}
                elif self.value() == 'month':
                    query = {kwarg_since: today, kwarg_until: next_month}
                elif self.value() == 'year':
                    query = {kwarg_since: today, kwarg_until: next_year}
                else:
                    query = {}
                return queryset.filter(**query)

        return ExpiryDateListFilter
