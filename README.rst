========
ItemList
========

ItemList is a customizable Django Admin ChangeList-like app for use outside of the admin.
It can be used to create versatile paginated lists of objects which can be searched, filtered
and provide links to detail pages similarly to the admin ChangeLists.

Provides a generic class-based view `ItemListView`.

ItemListView
------------

*class itemlist.views.ItemListView*
    A page representing a list of objects, with a search box, list filters, sortable columns, pagination and optional
    links to detailed pages.

    *Ancestors (MRO)*
        This view inherits methods and attributes from the following Django  views:

        * django.views.generic.list.ListView
        * django.views.generic.list.MultipleObjectTemplateResponseMixin
        * django.views.generic.base.TemplateResponseMixin
        * django.views.generic.list.BaseListView
        * django.views.generic.list.MultipleObjectMixin
        * django.views.generic.base.View

    *Methods and attributes*
        list_columns
            A list of field names to display in columns. Supports double underscore lookups.

        list_filters
            A list of field names or `django.contrib.admin.SimpleListFilter` instances for generating filters on the list.

        list_search
            A list of field names to include in search operations. Supports double underscore lookups.

        list_transforms
            A dictionary mapping field names to functions for transforming column values before display. Transform
            functions must take two arguments `transform(value, obj)`, where `obj` is the object corresponding
            to the list row.

        list_headers
            A dictionary mapping field names to header names for explicitly specifying the column header text.

        list_styles
            A dictionary mapping field names to css style classes to add to the HTML of the columns.

        list_title
            A string to use as the title of the list. If `None` (default), the model name is used.

        link_url
            A named url for creating links to detailed pages. If `None` (default), no links are created.

        link_kwarg
            The link kwarg parameter for `link_url`. Default is 'pk'

        link_attr
            By default links are created with the url in the href attribute of an anchor tag. The attribute can be
            changed by setting the link_attr parameter of the view. For example setting `link_attr` to `data-link` will
            create a tag that looks like `<a href="#!" data-link="http://...">...</a>`.  This is useful for loading
            content using JavaScript into modals or for ajax. This parameter replaces `link_data` boolean in previous
            versions.

        link_field
            Column name on which to create links. Must be one of the names included in list_columns. By default the
            first column will be used.

        get_list_columns()
            Return the field names to display in columns. By default, simply returns the value of `list_columns`.

        get_list_filters()
            Return the list_filters to display. By default, simply returns the value of `list_filters`.

        get_list_search()
            Return the list of field names to include in search operations. By default, simply returns the value
            of `list_search`.

        get_list_transforms()
            Return the dictionary of transforms to use for the columns. By default, simply returns the value of
            `list_transforms`.

        get_list_headers()
            Return the dictionary of column headings. By default, simply returns the value of `list_headers`.

        get_list_styles()
            Return the dictionary of column css styles. By default, simply returns the value of `list_styles`.

        get_list_title()
            Return the title of the list. By default, simply returns the value of `list_title`.

        get_link_url(obj)
            Return the detail url link for the current object/row. By default, uses the named url from `link_url`, the `kwarg` from
            `link_kwarg` and the value of the attribute.

        get_link_kwarg()
            Return the `kwarg` to use for the detail `link_url`. By default, simply returns the value of `link_kwarg`.

        get_link_field()
            Return the name of the column on which to create the detail links. By default, returns the first column.

        get_link_attr()
            Return the `attr` to use for the detail `link_url`. By default, simply returns the value of `link_attr`.


Example views.py:

.. code-block:: python

    from django.utils import timezone
    from itemlist import ItemListView

    from library.models import Topic

    class TopicList(ItemListView):
        template_name = 'myapp/topic_list.html'
        model = Topic
        list_filters = ['kind', 'parent']
        list_columns = ['id', 'name', 'acronym', 'kind', 'parent__name']
        list_search = ['name', 'kind__name']
        list_headers = {'parent__name': 'Mommy'}

        link_url = 'library:topic-detail'
        link_field = 'name'
        paginate_by = 20

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            context['now'] = timezone.now()
            return context

Example urls.py:

.. code-block:: python

    from django.urls import path

    from library.views import TopicList

    app_label = 'library'
    urlpatterns = [
        path('', TopicList.as_view(), name='topic-list'),
    ]

Examples for myapp/topic_list.html. The default template if none is specified is exactly the same as below:

.. code-block:: django

    {% extends "base.html" %}
    {% block content %}
        {% include "itemlist/embed_list.html" %}
    {% endblock %}


Another template example, equivalent to above. This allows you to reorder/omit components.

.. code-block:: django

    {% include "itemlist/filters.html" %}
    {% include "itemlist/list.html" %}
    {% include "itemlist/pagination.html" %}


