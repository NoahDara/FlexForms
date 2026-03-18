from django.db import models
from helpers.models import BaseModel

# Create your models here.

class DataType(BaseModel):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.name
    
class DataSource(BaseModel):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.name
    
class Data(BaseModel):
    source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='data')
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - ({self.source})"