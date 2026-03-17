from django import forms
from django.utils.safestring import mark_safe
from django.forms import DateInput, DateTimeInput, TimeInput
from django.db import IntegrityError
from django.core.exceptions import ValidationError


class FormErrorHandler:
    @staticmethod
    def get_formatted_errors(form):
        """
        Returns form errors in an HTML-formatted string with Bootstrap alert styles,
        including both field errors and non-field errors.
        """
        if not form.errors:
            return ""

        error_html = '<div class="example-alerts">'

        # Handle non-field errors first
        if form.non_field_errors():
            error_html += '<div class="example-alert">'
            error_html += (
                '<div class="alert alert-danger alert-icon alert-dismissible">'
                '<em class="icon ni ni-cross-circle"></em> '
                '<strong>Form error:</strong> '
            )
            for error in form.non_field_errors():
                error_html += f"{error} "
            error_html += '<button class="close" data-bs-dismiss="alert"></button>'
            error_html += "</div></div>"

        # Handle field-specific errors
        for field, errors in form.errors.items():
            if field == "__all__":
                continue

            error_html += '<div class="example-alert">'
            error_html += (
                '<div class="alert alert-danger alert-icon alert-dismissible">'
                '<em class="icon ni ni-cross-circle"></em> '
                f'<strong>{field.capitalize()}:</strong> '
            )

            for error in errors:
                error_html += f"{error} "

            error_html += '<button class="close" data-bs-dismiss="alert"></button>'
            error_html += "</div></div>"

        error_html += "</div>"
        return error_html


class CustomBaseForm(FormErrorHandler, forms.ModelForm):
    EXCLUDED_FIELDS = ["is_active", "is_deleted", "status", "is_available", "company"]
    INCLUDE_FIELDS: list = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Dynamically exclude unwanted fields
        effective_excluded = [
            f for f in self.EXCLUDED_FIELDS
            if f not in self.INCLUDE_FIELDS
        ]
        for field_name in effective_excluded:
            if field_name in self.fields:
                self.fields.pop(field_name)

        # Enhance widgets
        for name, field in self.fields.items():
            widget = field.widget

            # Apply special widgets based on field type
            if isinstance(field, forms.DateField):
                widget = DateInput(attrs={
                    "type": "date",
                    "class": "form-control",
                    "id": f"{name}-id"
                })
                self.fields[name].widget = widget

            elif isinstance(field, forms.DateTimeField):
                widget = DateTimeInput(attrs={
                    "type": "datetime-local",
                    "class": "form-control",
                    "id": f"{name}-id"
                })
                self.fields[name].widget = widget

            elif isinstance(field, forms.TimeField):
                widget = TimeInput(attrs={
                    "type": "time",
                    "class": "form-control",
                    "id": f"{name}-id"
                })
                self.fields[name].widget = widget

            # Apply existing styling rules
            elif isinstance(widget, forms.Textarea):
                widget.attrs.update({
                    "class": "form-control no-resize",
                    "id": f"{name}-id"
                })
            elif isinstance(field, forms.BooleanField):
                widget.attrs.update({
                    "class": "custom-control-input",
                    "id": f"{name}-id"
                })
            elif isinstance(field, forms.ModelMultipleChoiceField):
                widget.attrs.update({
                    "class": "form-select js-select2",
                    "multiple": "multiple",
                    "data-placeholder": "Select Multiple options",
                    "id": f"{name}-id"
                })
            elif isinstance(field, forms.ModelChoiceField):
                widget.attrs.update({
                    "class": "form-select js-select2",
                    "data-search": "on",
                    "data-allow-clear": "true",
                    "id": f"{name}-id"
                })
            else:
                # Only update default input fields if we didn't already replace the widget
                if not isinstance(field, (forms.DateField, forms.DateTimeField, forms.TimeField)):
                    widget.attrs.update({
                        "class": "form-control",
                        "id": f"{name}-id",
                    })

    def clean(self):
        """
        Override clean to validate model constraints before database insertion.
        This catches UniqueConstraint violations and uses violation_error_message.
        """
        cleaned_data = super().clean()
        
        # Don't validate constraints if there are already field errors
        if self.errors:
            return cleaned_data
        
        # Skip validation if instance doesn't have required fields yet
        # (this happens when excluded fields like 'company' are set later in form_valid)
        if not self._can_validate_constraints():
            return cleaned_data
        
        try:
            # Create a temporary instance with cleaned data
            instance = self.instance
            
            # Separate m2m fields from regular fields
            m2m_fields = []
            
            # Update instance with cleaned data (excluding many-to-many)
            for field_name, value in cleaned_data.items():
                try:
                    field = self._meta.model._meta.get_field(field_name)
                    
                    # Skip many-to-many fields - they need to be set after save
                    if field.many_to_many:
                        m2m_fields.append((field_name, value))
                        continue
                        
                    setattr(instance, field_name, value)
                except Exception:
                    # If field doesn't exist on model, skip it
                    continue
            
            # Validate constraints (this will raise ValidationError with violation_error_message)
            instance.validate_constraints()
            
        except ValidationError as e:
            # ValidationError from validate_constraints()
            # These contain our custom violation_error_message
            if hasattr(e, 'error_dict'):
                # Field-specific errors
                for field, errors in e.error_dict.items():
                    for error in errors:
                        if field == '__all__':
                            self.add_error(None, error)
                        else:
                            self.add_error(field, error)
            elif hasattr(e, 'error_list'):
                # Non-field errors - add as non-field errors
                for error in e.error_list:
                    self.add_error(None, error)
            else:
                # Fallback
                self.add_error(None, str(e))
        
        return cleaned_data
    
    def _can_validate_constraints(self):
        """
        Check if all required fields for constraint validation are present.
        Some fields (like 'company') might be excluded and set later in form_valid().
        """
        # Get all fields involved in constraints
        if not hasattr(self._meta.model._meta, 'constraints'):
            return True
        
        for constraint in self._meta.model._meta.constraints:
            if hasattr(constraint, 'fields'):
                for field_name in constraint.fields:
                    # If constraint field is not in form and instance doesn't have it yet
                    if field_name not in self.fields:
                        if not hasattr(self.instance, field_name) or getattr(self.instance, field_name) is None:
                            return False
        
        return True

    def save(self, commit=True):
        """
        Override save to catch IntegrityError as a safety net.
        This handles cases where constraints are violated despite form validation
        (e.g., race conditions, direct model saves, etc.)
        """
        if not commit:
            return super().save(commit=False)
        
        try:
            return super().save(commit=True)
        except IntegrityError as e:
            # Parse the error to provide meaningful feedback
            error_message = str(e)
            
            # Try to extract constraint name and provide helpful message
            if 'unique constraint' in error_message.lower() or 'UNIQUE constraint' in error_message:
                # Add as non-field error
                self.add_error(
                    None, 
                    'A record with these values already exists. Please check for duplicates.'
                )
            else:
                # Generic integrity error
                self.add_error(
                    None,
                    'A database constraint was violated. Please check your input and try again.'
                )
            
            # Re-raise ValidationError so Django treats this as invalid form
            from django.core.exceptions import ValidationError
            raise ValidationError('Constraint violation occurred')

    def render_form(self):
        # Separate fields into categories
        regular_fields = []   # includes normal inputs, many-to-many, foreign keys
        checkboxes = []       # boolean fields
        textareas_last = []   # textareas at the end

        for name, field in self.fields.items():
            bf = self[name]
            widget = field.widget

            # Textareas are collected last
            if isinstance(widget, forms.Textarea):
                textareas_last.append(self.render_textarea(bf, field.label))

            # Checkboxes collected separately
            elif isinstance(field, forms.BooleanField):
                checkboxes.append(self.render_boolean(bf, field.label))

            # Treat many-to-many and foreignkey as regular fields
            elif isinstance(field, (forms.ModelMultipleChoiceField, forms.ModelChoiceField)):
                regular_fields.append(self.render_input(bf, field.label))

            # Other inputs as regular fields
            else:
                regular_fields.append(self.render_input(bf, field.label))

        # Fix last element layout for regular fields if odd count
        if len(regular_fields) % 2 != 0:
            regular_fields[-1] = regular_fields[-1].replace('col-12 col-sm-6', 'col-12')

        # Build output in correct order
        html_output = []

        # Regular fields first
        if regular_fields:
            html_output.append('<div class="row g-3 regularfields-row">')
            html_output.extend(regular_fields)
            html_output.append('</div>')

        # Checkboxes after regular fields
        if checkboxes:
            html_output.append('<div class="row g-3 checkboxes-row mt-2">')
            html_output.extend(checkboxes)
            html_output.append('</div>')

        # Textareas always last
        if textareas_last:
            html_output.append('<div class="row g-3 textarea-row mt-2">')
            html_output.extend(textareas_last)
            html_output.append('</div>')

        return mark_safe("".join(html_output))

    def render_textarea(self, field, label):
        return f'''
        <div class="col-12">
            <div class="form-group">
                <label class="form-label" for="{field.auto_id}">{label}</label>
                <div class="form-control-wrap">
                    {field}
                </div>
            </div>
        </div>
        '''

    def render_input(self, field, label):
        # Add required marker
        required_marker = '<span class="text-danger">*</span>' if field.field.required else ""

        error_html = ""
        if field.errors:
            error_html = f'<div class="invalid-feedback d-block">{" ".join(field.errors)}</div>'

        help_html = ""
        if field.field.help_text:
            help_html = f'<small class="form-text text-muted">{field.field.help_text}</small>'

        return f'''
        <div class="col-12 col-sm-6">
            <div class="form-group">
                <label class="form-label" for="{field.auto_id}">{label} {required_marker}</label>
                <div class="form-control-wrap">
                    {field}
                    {error_html}
                    {help_html}
                </div>
            </div>
        </div>
        '''

    def render_boolean(self, field, label):
        help_html = ""
        if field.field.help_text:
            help_html = f'<small class="form-text text-muted d-block mt-2">{field.field.help_text}</small>'
        
        checked = 'checked' if field.value() else ''
        
        return f'''
        <div class="col-12 col-sm-6 col-md-3">
            <div class="preview-block">
                <div class="custom-control custom-checkbox">
                    <input type="checkbox" class="custom-control-input" id="{field.auto_id}" name="{field.html_name}" {checked}>
                    <label class="custom-control-label" for="{field.auto_id}">{label}</label>
                </div>
                {help_html}
            </div>
        </div>
        '''

    def render_manytomany(self, field, label):
        return f'''
        <div class="col-12 col-sm-6">
            <div class="form-group">
                <label class="form-label">{label}</label>
                <div class="form-control-wrap">
                    {field}
                </div>
            </div>
        </div>
        '''

    def render_foreignkey(self, field, label):
        return f'''
        <div class="col-12 col-sm-6">
            <div class="form-group">
                <label class="form-label">{label}</label>
                <div class="form-control-wrap">
                    {field}
                </div>
            </div>
        </div>
        '''
        
    def get_error_html(self):
        return FormErrorHandler.get_formatted_errors(self)