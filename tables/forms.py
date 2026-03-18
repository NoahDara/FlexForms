from helpers.forms import CustomBaseForm
from .models import Table, TableColumn, TableRow, TableCellConfig

class TableForm(CustomBaseForm):
    class Meta:
        model = Table
        fields = "__all__"