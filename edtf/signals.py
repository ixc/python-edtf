from django.db.models import signals
from django.db.models.loading import get_models


def get_nested_subclasses(cls):
    result = [cls]
    classes_to_inspect = [cls]
    while classes_to_inspect:
        class_to_inspect = classes_to_inspect.pop()
        for subclass in class_to_inspect.__subclasses__():
            if subclass not in result:
                result.append(subclass)
                classes_to_inspect.append(subclass)
    return result


# register the signal for all subclasses of all models that have
# EDTFFields.
for model in get_models():
    fields = getattr(model, 'edtf_fields', [])
    subclasses = get_nested_subclasses(model)
    for field in fields:
        for subclass in subclasses:
            signals.pre_save.connect(field.pre_save_update,
                                         sender=subclass)

