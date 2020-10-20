from django import template
from django.core.exceptions import ObjectDoesNotExist, FieldDoesNotExist
from django.db import models
from django.utils.encoding import smart_str
from django.utils.html import mark_safe, escape
from django.utils import timezone
register = template.Library()


@register.inclusion_tag('itemlist/row.html', takes_context=True)
def show_row(context, obj):
    return {
        'fields': context['view'].get_row(obj)
    }


@register.inclusion_tag('itemlist/filters.html', takes_context=True)
def itemlist_filters(context):
    return context


@register.simple_tag(takes_context=True)
def itemlist_heading(context):
    view = context['view']
    return view.get_list_title()


@register.inclusion_tag('itemlist/list.html', takes_context=True)
def itemlist_list(context):
    return context


@register.simple_tag(takes_context=True)
def show_grid_cell(context, obj):
    context['object'] = obj
    t = template.loader.get_template(context['view'].get_grid_template(obj))
    return mark_safe(t.render(context))


def get_row_values(obj, view):
    list_display = view.get_list_display()
    opts = obj._meta
    if not list_display:
        yield {'data': obj, 'style': ''}

    for field_name in list_display:
        try:
            field = opts.get_field(field_name)
        except FieldDoesNotExist:
            # For non-field list_display values, the value is either a method
            # or a property.
            try:
                field_lookups = field_name.split('__')
                attr = obj
                for name in field_lookups:
                    attr = getattr(attr, name, '')

                allow_tags = getattr(attr, 'allow_tags', True)
                if callable(attr):
                    attr = attr()
                if field_name in view.list_transforms:
                    result_repr = mark_safe(view.list_transforms[field_name](attr, obj))
                else:
                    result_repr = smart_str(attr)
            except (AttributeError, ObjectDoesNotExist):
                result_repr = ''
            else:
                # Strip HTML tags in the resulting text, except if the
                # function has an "allow_tags" attribute set to True.
                if not allow_tags:
                    result_repr = escape(result_repr)
        else:
            field_val = getattr(obj, field.attname)
            if field_name in view.list_transforms:
                result_repr = mark_safe(view.list_transforms[field_name](field_val, obj))
            elif isinstance(field.rel, models.ManyToOneRel):
                if field_val is not None:
                    try:
                        result_repr = escape(getattr(obj, field.name))
                    except (AttributeError, ObjectDoesNotExist):
                        result_repr = ''
                else:
                    result_repr = ''

            # Dates and times are special: They're formatted in a certain way.
            elif isinstance(field, models.DateField) or isinstance(field, models.TimeField):
                if field_val:
                    if isinstance(field, models.DateTimeField):
                        result_repr = timezone.localtime(field_val).strftime('%c')
                    elif isinstance(field, models.TimeField):
                        result_repr = field_val.strftime('%X')
                    elif isinstance(field, models.DateField):
                        result_repr = field_val.strftime('%Y-%m-%d')
                    else:
                        result_repr = ""
                else:
                    result_repr = ''
            # Booleans are special: We use images.
            elif isinstance(field, models.BooleanField) or isinstance(field, models.NullBooleanField):
                result_repr = _boolean_icon(field_val)
            # DecimalFields are special: Zero-pad the decimals.
            elif isinstance(field, models.DecimalField):
                if field_val is not None:
                    result_repr = ('%%.%sf' % field.decimal_places) % field_val
                else:
                    result_repr = ''
            # Fields with choices are special: Use the representation
            # of the choice.
            elif field.choices:
                m_name = 'get_{0}_display'.format(field_name)
                result_repr = getattr(obj, m_name)()
            else:
                result_repr = escape(smart_str(field_val))

        yield {'data': result_repr, 'style': view.list_styles.get(field_name, '')}


def _boolean_icon(field_val):
    if field_val:
        return mark_safe('&check;')
    else:
        return ''
