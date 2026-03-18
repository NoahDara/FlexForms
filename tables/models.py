from django.db import models
from helpers.models import BaseModel
from django.core.exceptions import ValidationError
 
 
class Table(BaseModel):
    """
    A reusable table definition that can be embedded inside any form as a
    table field. TableConfigs are global — they are created independently and
    can be linked to multiple FormFields across different forms.
 
    There are two table types:
 
      DYNAMIC_ROWS:
        Admin defines column headers only. Users fill in as many rows as they
        need at submission time. Suitable for open-ended lists such as
        employment history or family members.
 
      FIXED_GRID:
        Admin defines both column headers AND row labels. The grid is fully
        fixed — users only fill in the cell values. Each cell can have its own
        data type. Suitable for structured matrices such as monthly ratings or
        skill assessments.
    """    
    
    
    TABLE_TYPE_CHOICES = (
        ('dynamic_rows', 'Dynamic Rows'),
        ("fixed_grid", "Fixed Grid")
    )
 
    name = models.CharField(max_length=255, unique=True, help_text="Human-readable name for this table e.g. 'Employment History Table'",)
    description = models.TextField( blank=True, null=True,  help_text="Optional description of what this table captures",)
    
    table_type = models.CharField( max_length=20, choices=TABLE_TYPE_CHOICES, default='dynamic_rows',
        help_text="Whether users can add rows freely or the grid is fixed by the admin",
    )
 
 
    def __str__(self):
        return f"{self.name} ({self.get_table_type_display()})"
    
    
class TableColumn(BaseModel):
    """
    Defines a single column inside a TableConfig.
 
    Each column has a header label and a data type that controls what kind of
    input is shown in that column's cells. For choice-based column types such
    as dropdown or radio, a DataSource can be linked to provide the options.
 
    Columns are ordered via the 'order' field.
    """
 
 
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="columns",  help_text="The table this column belongs to",)
    header = models.CharField(max_length=255, help_text="The column header label displayed to the user e.g. 'Company Name'",)
    data_type = models.ForeignKey("data.DataType", on_delete=models.CASCADE, help_text="The data type for cells in this column", related_name="table_columns")
    order = models.PositiveIntegerField(default=0,
        help_text="Display order of this column within the table (left to right)",)
 
    is_required = models.BooleanField( default=False, help_text="Whether cells in this column must be filled in",)
 
    data_source = models.ForeignKey("data.DataSource", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="table_columns", help_text="Required when column_type is dropdown or radio", )
    
    RELATIONAL_DATA_TYPES = {"foreign_key", "many_to_many"}
 
    class Meta(BaseModel.Meta):
        ordering = ["order"]
 
    def __str__(self):
        return f"{self.table.name} — {self.header}"
    
    def clean(self):
        super().clean()
        if (
            hasattr(self, "data_type")
            and self.data_type.code in self.RELATIONAL_DATA_TYPES
            and not self.data_source
        ):
            raise ValidationError({
                "data_source": (
                    f"A data source is required when the data type is "
                    f"'{self.data_type.name}'. Please link a data source to provide selectable options."
                )
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    
class TableRow(BaseModel):
    """
    Defines a named row inside a FIXED_GRID TableConfig.
 
    Row labels are set by the admin when configuring the table. Users cannot
    add or remove rows — they only fill in the cell values for each defined row.
 
    Only used when TableConfig.table_type is FIXED_GRID.
    """
 
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="rows",  help_text="The fixed grid table this row belongs to",)
    row_label = models.CharField(max_length=255, help_text="The row label displayed on the left side e.g. 'Service Quality'",)
    order = models.PositiveIntegerField(default=0, help_text="Display order of this row within the table (top to bottom)",)
 
    class Meta(BaseModel.Meta):
        ordering = ["order"]
 
    def __str__(self):
        return f"{self.table.name} — {self.row_label}"
    
    
class TableCell(BaseModel):
    """
    Defines the configuration for a specific cell in a FIXED_GRID table,
    identified by its row and column intersection.
 
    By default a cell inherits its type from the column. This model allows
    overriding the type at the individual cell level when needed — for example
    a grid where most cells are numbers but one specific cell is a dropdown.
 
    Only used when TableConfig.table_type is FIXED_GRID.
    """
 
    table = models.ForeignKey(Table, on_delete=models.CASCADE, related_name="cell_configs", help_text="The fixed grid table this cell config belongs to",)
    row = models.ForeignKey(TableRow,  on_delete=models.CASCADE, related_name="cell_configs", help_text="The row this cell sits in",)
    column = models.ForeignKey(TableColumn, on_delete=models.CASCADE, related_name="cell_configs", help_text="The column this cell sits in",)
    data_type = models.ForeignKey("data.DataType", related_name="cell_configs", on_delete=models.CASCADE,
        help_text=(
            "Optional override for the cell data type. "
            "If blank the column type is used."
        ),
    )
 
    data_source = models.ForeignKey("data.DataSource", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="cell_configs", help_text="Required when cell_type overrides to dropdown or radio",)
    
    RELATIONAL_DATA_TYPES = {"foreign_key", "many_to_many"}
 
    class Meta(BaseModel.Meta):
        unique_together = [("table", "row", "column")]
 
    def __str__(self):
        return f"{self.table.name} — row: {self.row.row_label} / col: {self.column.header}"
    

    def clean(self):
        super().clean()
        if (
            hasattr(self, "data_type")
            and self.data_type.code in self.RELATIONAL_DATA_TYPES
            and not self.data_source
        ):
            raise ValidationError({
                "data_source": (
                    f"A data source is required when the data type is "
                    f"'{self.data_type.name}'. Please link a data source to provide selectable options."
                )
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)