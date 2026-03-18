from helpers.forms import CustomBaseForm
from .models import Table, TableColumn, TableRow, TableCell

class TableForm(CustomBaseForm):
    class Meta:
        model = Table
        fields = "__all__"
        
class TableColumnForm(CustomBaseForm):
    class Meta:
        model = TableColumn
        fields = "__all__"
        exclude = ['table',]
        
class TableRowForm(CustomBaseForm):
    class Meta:
        model = TableRow
        fields = "__all__"
        exclude = ['table',]
        
class TableCellForm(CustomBaseForm):
    class Meta:
        model = TableCell
        fields = "__all__"
        exclude = ['table',]