from django.contrib import admin
from .models import Form, FormSection, FormField


class FormSectionInline(admin.TabularInline):
    model = FormSection
    extra = 0
    fields = ["name", "description", "order", "is_active"]
    ordering = ["order"]


class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 0
    fields = ["label", "data_type", "section", "order", "is_required", "data_source", "table", "is_active"]
    ordering = ["order"]


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ["title", "requires_login", "is_published", "is_active", "created", "updated"]
    list_filter = ["is_published", "requires_login", "is_active"]
    search_fields = ["title", "description"]
    readonly_fields = ["uid", "created", "updated"]
    inlines = [FormSectionInline, FormFieldInline]
    fieldsets = (
        ("General", {
            "fields": ("uid", "title", "description")
        }),
        ("Access & Visibility", {
            "fields": ("requires_login", "is_published")
        }),
        ("Status", {
            "fields": ("is_active", "is_deleted")
        }),
        ("Timestamps", {
            "fields": ("created", "updated"),
            "classes": ("collapse",)
        }),
    )


@admin.register(FormSection)
class FormSectionAdmin(admin.ModelAdmin):
    list_display = ["name", "form", "order", "is_active", "created"]
    list_filter = ["is_active", "form"]
    search_fields = ["name", "form__title"]
    readonly_fields = ["uid", "created", "updated"]
    autocomplete_fields = ["form"]
    fieldsets = (
        ("General", {
            "fields": ("uid", "form", "name", "description", "order")
        }),
        ("Status", {
            "fields": ("is_active", "is_deleted")
        }),
        ("Timestamps", {
            "fields": ("created", "updated"),
            "classes": ("collapse",)
        }),
    )


@admin.register(FormField)
class FormFieldAdmin(admin.ModelAdmin):
    list_display = ["label", "form", "section", "data_type", "order", "is_required", "is_active", "created"]
    list_filter = ["is_required", "is_active", "data_type", "form"]
    search_fields = ["label", "form__title", "section__name"]
    readonly_fields = ["uid", "created", "updated"]
    autocomplete_fields = ["form", "section", "data_type", "data_source", "table"]
    fieldsets = (
        ("General", {
            "fields": ("uid", "form", "section", "label", "order")
        }),
        ("Field Configuration", {
            "fields": ("data_type", "is_required", "help_text")
        }),
        ("Data Linking", {
            "fields": ("data_source", "table"),
            "description": "Link a data source for relational types, or a table for table field types."
        }),
        ("Status", {
            "fields": ("is_active", "is_deleted")
        }),
        ("Timestamps", {
            "fields": ("created", "updated"),
            "classes": ("collapse",)
        }),
    )