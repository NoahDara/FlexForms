from django.contrib import admin
from .models import DataType, DataSource, Data
from simple_history.admin import SimpleHistoryAdmin

@admin.register(DataType)
class DataTypeAdmin(SimpleHistoryAdmin):
    list_display = ('code', 'name', 'description')
    search_fields = ('code', 'name')

@admin.register(DataSource)
class DataSourceAdmin(SimpleHistoryAdmin):
    list_display = ('code', 'name', 'description')
    search_fields = ('code', 'name')

@admin.register(Data)
class DataAdmin(SimpleHistoryAdmin):
    list_display = ('name', 'source', 'description')
    search_fields = ('name',)
    list_filter = ('source',)