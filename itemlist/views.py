import operator
import re
from collections import OrderedDict
from datetime import date, datetime, time
from django.contrib import admin
from django.contrib.admin import FieldListFilter
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.utils import get_fields_from_path, prepare_lookup_value
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.urls import reverse_lazy
from django.utils import timezone, safestring
from django.utils.encoding import force_str
from django.utils.http import urlencode
from django.views.generic import ListView
from functools import reduce

try:
    from django.contrib.admin.utils import lookup_needs_distinct
except ImportError:
    from django.contrib.admin.utils import lookup_spawns_duplicates as lookup_needs_distinct 

ALL_VAR = 'all'
ORDER_VAR = 'order'
PAGE_VAR = 'page'
SEARCH_VAR = 'search'
CSV_VAR = 'csv'
GRID_VAR = 'grid'


def get_column_title(model, name):
    opts = model._meta
    if '__' not in name:
        try:
            return opts.get_field(name).verbose_name.title()
        except FieldDoesNotExist:
            # For non-field list_display values, check for the function
            # attribute "short_description". If that doesn't exist, fall back
            # to the method name.
            attr = getattr(model, name, '')
            try:
                header = attr.short_description
            except AttributeError:
                header = name.replace('_', ' ')
            return header.title()
    else:
        this, rest = name.split('__', 1)
        field = opts.get_field(this)
        return field.verbose_name.title() + ' / ' + get_column_title(field.related_model(), rest)


class ItemListView(ListView):
    list_filters = []
    list_columns = []
    list_headers = {}
    list_transforms = {}
    list_styles = {}
    list_search = []
    list_title = ""

    link_url = None
    link_kwarg = 'pk'
    link_attr = None
    link_field = None

    ordering = []

    template_name = "itemlist/item_list.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column_attrs = {}
        self.filter_specs = None
        self.has_filters = False

    def get_list_columns(self):
        return self.list_columns

    def get_list_headers(self):
        return self.list_headers

    def get_list_transforms(self):
        return self.list_transforms

    def get_list_filters(self):
        return self.list_filters

    def get_list_search(self):
        return self.list_search

    def get_list_styles(self):
        return self.list_styles

    def get_link_kwarg(self):
        return self.link_kwarg

    def get_link_field(self):
        columns = self.get_list_columns()
        return self.link_field if self.link_field is not None else columns[0]

    def get_link_url(self, obj):
        if self.link_url:
            return reverse_lazy(self.link_url, kwargs={self.get_link_kwarg(): getattr(obj, self.get_link_kwarg())})
        else:
            return None

    def get_list_title(self):
        return self.list_title if self.list_title else self.model._meta.verbose_name_plural.title()

    def get_link_attr(self, obj):
        return self.link_attr

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query_string'] = self.get_query_string(remove=[PAGE_VAR, CSV_VAR])
        context['headers'] = self.get_headers()
        context['num_columns'] = len(self.get_list_columns())
        context['filters'] = [self.get_filter_data(spec) for spec in self.filter_specs]
        context['has_filters'] = self.has_filters
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        self.model = qs.model
        self.column_attrs = OrderedDict()
        annotation = {}
        for i, field_name in enumerate(self.get_list_columns()):
            if '__' in field_name:
                name = '_column_{}'.format(i)
                self.column_attrs[field_name] = name
                annotation[name] = models.F(field_name)
            else:
                self.column_attrs[field_name] = field_name

        params = dict(self.request.GET.items())
        search_text = params.get(SEARCH_VAR, '')

        # First, we collect all the declared list filters.
        self.filter_specs, has_filters, filter_use_distinct = self.get_filters()
        # Then, we let every list filter modify the queryset to its liking.
        for filter_spec in self.filter_specs:
            new_qs = filter_spec.queryset(self.request, qs)
            qs = new_qs if new_qs is not None else qs

        # Search
        search_use_distinct = False
        if search_text:
            qs, search_use_distinct = self.get_search_results(qs, search_text)

        self.has_filters = bool(search_text) or has_filters

        # add annotations for related entries in other tables
        qs = qs.annotate(**annotation)

        # Set ordering.
        qs = qs.order_by(*self.get_ordering())

        # Remove duplicates from results, if necessary
        if search_use_distinct or filter_use_distinct:
            qs = qs.distinct()

        # determine related fields and select and/or prefetch related fields
        to_select = []
        to_prefetch = []
        for column in self.get_list_columns():
            field_name = column.split('__')[0]
            try:
                field = self.model._meta.get_field(field_name)
            except FieldDoesNotExist:
                # not a field, perhaps a method or an annotation
                pass
            else:
                if isinstance(field, models.ForeignKey):
                    to_select.append(field_name)
                elif isinstance(field, models.ManyToManyField):
                    to_prefetch.append(field_name)

        if to_select:
            qs = qs.select_related(*to_select)

        if to_prefetch:
            qs = qs.prefetch_related(*to_prefetch)

        return qs

    def get_ordering(self):
        """
        Returns the list of ordering fields for the object list.
        First we check the object's default ordering. Then, any manually-specified ordering
        from the query string overrides anything. Finally, a deterministic
        order is guaranteed by ensuring the primary key is used as the last
        ordering field.
        """

        params = dict(self.request.GET.items())
        ordering_text = params.get(ORDER_VAR, '')
        ordering = super().get_ordering()
        if ordering_text:
            ordering = []
            column_fields = list(self.column_attrs.values())
            columns = ordering_text.split('.')
            for order_field in columns:
                try:
                    prefix, index = order_field.rpartition('-')[1:]
                    field_name = column_fields[int(index)]
                    ordering.append(prefix + field_name)
                except (IndexError, ValueError):
                    continue  # Invalid ordering specified, skip it.

        # Ensure that the primary key is systematically present in the list of
        # ordering fields so we can guarantee a deterministic order across all
        # database backends.

        if not (set(ordering) & {'pk', '-pk'}):
            ordering.append('-pk')
        return ordering

    def get_query_string(self, new_params=None, remove=None):
        """
        Determine the persistent part of the query string for use in the template
        :param new_params: query parameters to add
        :param remove: query parameters to remove
        :return: urlencoded querystring, including initial '?'
        """
        if new_params is None: new_params = {}
        if remove is None: remove = []
        params = dict(self.request.GET.items())
        remove.extend([PAGE_VAR])
        for r in remove:
            for k in list(params):
                if k.startswith(r):
                    del params[k]
        for k, v in new_params.items():
            if v is None:
                if k in params:
                    del params[k]
            else:
                params[k] = v
        return '?{}'.format(urlencode(sorted(params.items())))

    def get_search_results(self, queryset, search_term):
        """
        Generate a queryset according to the search term. Words in the search term are searched using the OR operator
        :param queryset: queryset to filter
        :param search_term: search string
        :return: tuple (queryset, distinct), distinct will be True if queryset is likely to contain duplicates
        """
        def construct_search(field_name):
            if field_name.startswith('^'):
                return "{}__istartswith".format(field_name[1:])
            elif field_name.startswith('='):
                return "{}__iexact".format(field_name[1:])
            elif field_name.startswith('@'):
                return "{}__search".format(field_name[1:])
            else:
                return "{}__icontains".format(field_name)

        opts = queryset.model._meta
        search_fields = self.get_list_search()
        use_distinct = False
        if search_fields and search_term:
            orm_lookups = [construct_search(str(search_field)) for search_field in search_fields]
            queryset = queryset.filter(
                reduce(operator.or_, [
                    models.Q(**{orm_lookup: bit}) for bit in search_term.split() for orm_lookup in orm_lookups
                ])
            )
            use_distinct = any(lookup_needs_distinct(opts, search_spec) for search_spec in orm_lookups)
        return queryset, use_distinct

    def get_headers(self):
        """
        Generate headers for each field in `list_columns`. The header is a dictionary
        with fields `text`, which contains the text to display and optionally `style`,
        which contains the corresponding style from `list_styles`.

        Generate urls for multi-sorting. The urls work as a 3-state toggle in the order
        of sort-ascending, sort-descending, do not sort by column -- that is, remove
        column from multi-sort specification.
        """
        params = dict(self.request.GET.items())
        ordering_text = params.get(ORDER_VAR, '')

        order_specs = OrderedDict([
            (int(re.sub(r"\D", "", c)), '-' if c[0] == '-' else '')
            for c in ordering_text.split('.') if c
        ])

        list_headers = self.get_list_headers()

        for i, field_name in enumerate(self.get_list_columns()):
            # generate new url for sorting through the table header
            # '': sorted asc, '-':sorted desc, '*': not sorted (ignore tag)

            sort_style = {'-': 'sorted-dn', '': 'sorted-up', '*': 'not-sorted'}[order_specs.get(i, '*')]
            field_tag = ({'': '-', '-': '*', '*': ''}[order_specs.get(i, '*')], i)
            rest_tags = [(v, k) for k, v in order_specs.items() if k != i]
            sort_val = '.'.join(['{0}{1}'.format(d, c) for d, c in [field_tag] + rest_tags if d != '*'])
            header_url = self.get_query_string(new_params={ORDER_VAR: sort_val})

            header_text = list_headers.get(field_name, get_column_title(self.model, field_name))
            styles = self.get_list_styles()

            header = {
                "text": header_text,
                'style': ' '.join([sort_style, styles.get(field_name, '')]),
                'url': header_url
            }
            yield header

    def get_row(self, obj):
        """
        Generator for returning the text corresponding to the column values for a given row
        :param obj: the row item
        :return: dict
        """
        list_columns = self.get_list_columns()
        opts = obj._meta
        if not list_columns:
            yield {'data': obj, 'style': ''}
        transforms = self.get_list_transforms()
        styles = self.get_list_styles()
        link_field = self.get_link_field()

        for field_name in list_columns:
            try:
                field = opts.get_field(field_name)
            except FieldDoesNotExist:
                # For non-field list_display values, the value is either a method
                # or a property
                field = None

            attr_name = self.column_attrs[field_name]
            value = getattr(obj, attr_name, '')
            if callable(value):
                value = value()

            if field_name in transforms:
                value = safestring.mark_safe(transforms[field_name](value, obj))

            if isinstance(value, datetime):
                value = timezone.localtime(value).strftime('%c')
            elif isinstance(value, time):
                value =  value.strftime('%X')
            elif isinstance(value, date):
                value = value.strftime('%Y-%m-%d')
            elif field and field.choices:
                choice_method = 'get_{}_display'.format(field_name)
                value = getattr(obj, choice_method)()
            elif value is None:
                value = ''
            else:
                value = str(value)

            # replace text with link for link field of column
            if field_name == link_field:
                url = self.get_link_url(obj)
                attr = self.get_link_attr(obj)
                if url:
                    if attr and attr != "href":
                        value = safestring.mark_safe('<a href="#!" {attr}="{url}">{value}</a>'.format(url=url, value=value, attr=attr))
                    else:
                        value = safestring.mark_safe('<a href="{href}">{value}</a>'.format(href=url, value=value))

            yield {'text': value, 'style': styles.get(field_name, '')}

    def get_filter_data(self, flt):
        title = flt.title
        choices = list(flt.choices(self))
        selected = [choice['display'] for choice in choices if choice['selected']][0]
        return title, choices, selected

    def get_filters(self):
        params = dict(self.request.GET.items())
        opts = self.model._meta
        use_distinct = False
        list_filters = self.get_list_filters()
        new_params = {}
        has_filters = False

        # Normalize the types of keys
        list_names = [f if isinstance(f, str) else f.parameter_name for f in list_filters]
        for key, value in params.items():
            # ignore keys not in list_filters
            if key.startswith(tuple(list_names)):
                new_params[force_str(key)] = value

        has_filters = bool(new_params)
        filter_specs = []
        for list_filter in list_filters:
            if callable(list_filter):
                # This is simply a custom list filter class.
                spec = list_filter(self.request, new_params, self.model, None)
            else:
                field_path = None
                if isinstance(list_filter, (tuple, list)):
                    # Custom FieldListFilter class for a given field.
                    field, field_list_filter_class = list_filter
                else:
                    # Field name, so use the default registered FieldListFilter
                    field, field_list_filter_class = list_filter, FieldListFilter.create

                if not isinstance(field, models.Field):
                    field_path = field
                    field = get_fields_from_path(self.model, field_path)[-1]
                model_admin = admin.ModelAdmin(self.model, admin.site)
                spec = field_list_filter_class(field, self.request, new_params, self.model, model_admin, field_path=field_path)
                # Check if we need to use distinct()
                use_distinct = (use_distinct or lookup_needs_distinct(opts, field_path))
            if spec and spec.has_output():
                filter_specs.append(spec)

        # All the parameters used by the various ListFilters have been removed
        # lookup_params, now only contains other parameters passed via the query string.
        # We now loop through the remaining parameters both to ensure that all the parameters are valid
        # fields and to determine if at least one of them needs distinct(). If
        # the lookup parameters aren't real fields, then bail out.
        try:
            for key, value in new_params.items():
                new_params[key] = prepare_lookup_value(key, value)
                use_distinct = (use_distinct or lookup_needs_distinct(opts, key))
            return filter_specs, has_filters, use_distinct
        except FieldDoesNotExist as e:
            raise IncorrectLookupParameters from e
