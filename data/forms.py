from helpers.forms import CustomBaseForm
from .models import DataSource, Data

class DataSourceForm(CustomBaseForm):
    class Meta:
        model = DataSource
        fields = "__all__"
        
class DataForm(CustomBaseForm):
    class Meta:
        model = Data
        fields = "__all__"
        exclude = ['source',]