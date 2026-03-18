from helpers.forms import CustomBaseForm
from .models import Form, FormSection, FormField


class FormForm(CustomBaseForm):
    class Meta:
        model = Form
        fields = "__all__"
        exclude = ['is_published',]
        
class FormSectionForm(CustomBaseForm):
    class Meta:
        model = FormSection
        fields = "__all__"
        exclude = ['form',]
        
class FormFieldForm(CustomBaseForm):
    class Meta:
        model = FormField
        fields = "__all__"
        exclude = ['form',]