from django.contrib import admin

from .models import TestEvent


class TestEventAdmin(admin.ModelAdmin):
    list_display = (
        "date_display",
        "date_edtf_direct",
        "date_earliest",
        "date_latest",
        "date_sort_ascending",
        "date_sort_descending",
        "date_edtf",
    )
    search_fields = ("date_display", "date_edtf_direct")
    list_filter = ("date_earliest", "date_latest")
    readonly_fields = (
        "date_earliest",
        "date_latest",
        "date_sort_ascending",
        "date_sort_descending",
        "date_edtf",
    )

    fieldsets = (
        (None, {"fields": ("date_display", "date_edtf_direct", "date_edtf")}),
        (
            "Computed Dates",
            {
                "classes": ("collapse",),
                "fields": (
                    "date_earliest",
                    "date_latest",
                    "date_sort_ascending",
                    "date_sort_descending",
                ),
            },
        ),
    )


admin.site.register(TestEvent, TestEventAdmin)
