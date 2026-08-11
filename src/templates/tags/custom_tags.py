from django import template

register = template.Library()

PAGE_PARAMS = {"page", "o", "page_size"}


@register.simple_tag
def group_params(request):
    filter_params = []
    page_params = []

    for name, values in request.GET.lists():
        if name in PAGE_PARAMS:
            page_params.append((name, values))
            continue

        filter_params.append((name, values))

    return {
        "filters": filter_params,
        "page": page_params,
    }


@register.filter
def verbose_name(model, field_name=None):
    if field_name:
        field = model._meta.get_field(field_name)
        return field.verbose_name

    return model._meta.verbose_name


@register.filter
def verbose_name_plural(model, field_name=None):
    if field_name:
        field = model._meta.get_field(field_name)
        return field.verbose_name_plural

    return model._meta.verbose_name_plural


@register.filter
def getlist(querydict, key):
    return querydict.getlist(key)


@register.filter
def list_remove(values, item):
    return [v for v in values if v != item]


@register.filter
def as_dict(value, key):
    return {key: value}
