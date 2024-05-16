# Generated by Django 4.2.13 on 2024-05-09 18:13

from django.db import migrations, models
import edtf.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="TestEvent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "date_display",
                    models.CharField(
                        blank=True,
                        help_text="Enter the date in natural language format (e.g., 'Approximately June 2004').",
                        max_length=255,
                        null=True,
                        verbose_name="Date of creation (display)",
                    ),
                ),
                (
                    "date_edtf_direct",
                    models.CharField(
                        blank=True,
                        help_text="Enter the date in EDTF format (e.g., '2004-06~').",
                        max_length=255,
                        null=True,
                        verbose_name="Date of creation (EDTF format)",
                    ),
                ),
                (
                    "date_edtf",
                    edtf.fields.EDTFField(
                        blank=True,
                        lower_fuzzy_field="date_earliest",
                        lower_strict_field="date_sort_ascending",
                        natural_text_field="date_display",
                        null=True,
                        upper_fuzzy_field="date_latest",
                        upper_strict_field="date_sort_descending",
                        verbose_name="Date of creation (EDTF)",
                    ),
                ),
                ("date_earliest", models.FloatField(blank=True, null=True)),
                ("date_latest", models.FloatField(blank=True, null=True)),
                ("date_sort_ascending", models.FloatField(blank=True, null=True)),
                ("date_sort_descending", models.FloatField(blank=True, null=True)),
            ],
        ),
    ]