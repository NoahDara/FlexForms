from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Table, TableColumn, TableRow, TableCellConfig


class TableColumnInline(admin.TabularInline):
    model = TableColumn
    extra = 1
    fields = ('header', 'column_type', 'order', 'is_required', 'data_source')
    ordering = ('order',)


class TableRowInline(admin.TabularInline):
    model = TableRow
    extra = 1
    fields = ('row_label', 'order')
    ordering = ('order',)


class TableCellConfigInline(admin.TabularInline):
    model = TableCellConfig
    extra = 0
    fields = ('row', 'column', 'cell_type', 'data_source')


@admin.register(Table)
class TableAdmin(SimpleHistoryAdmin):
    list_display = ('name', 'table_type', 'created', 'updated', 'is_active')
    list_filter = ('table_type', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('uid', 'created', 'updated')
    inlines = [TableColumnInline, TableRowInline]
    fieldsets = (
        (None, {
            'fields': ('uid', 'name', 'description', 'table_type')
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TableColumn)
class TableColumnAdmin(SimpleHistoryAdmin):
    list_display = ('header', 'table', 'column_type', 'order', 'is_required', 'data_source', 'is_active')
    list_filter = ('is_required', 'is_active', 'column_type')
    search_fields = ('header', 'table__name')
    readonly_fields = ('uid', 'created', 'updated')
    autocomplete_fields = ('table', 'column_type', 'data_source')
    fieldsets = (
        (None, {
            'fields': ('uid', 'table', 'header', 'column_type', 'order', 'is_required', 'data_source')
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TableRow)
class TableRowAdmin(SimpleHistoryAdmin):
    list_display = ('row_label', 'table', 'order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('row_label', 'table__name')
    readonly_fields = ('uid', 'created', 'updated')
    autocomplete_fields = ('table',)
    fieldsets = (
        (None, {
            'fields': ('uid', 'table', 'row_label', 'order')
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TableCellConfig)
class TableCellConfigAdmin(SimpleHistoryAdmin):
    list_display = ('table', 'row', 'column', 'cell_type', 'data_source', 'is_active')
    list_filter = ('is_active', 'cell_type')
    search_fields = ('table__name', 'row__row_label', 'column__header')
    readonly_fields = ('uid', 'created', 'updated')
    autocomplete_fields = ('table', 'row', 'column', 'cell_type', 'data_source')
    fieldsets = (
        (None, {
            'fields': ('uid', 'table', 'row', 'column', 'cell_type', 'data_source')
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        }),
    )