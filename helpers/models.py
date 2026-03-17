from django.db import models
import uuid
from django.contrib.contenttypes.models import ContentType
from simple_history.utils import update_change_reason
from simple_history.models import HistoricalRecords

from helpers.utilities import can_export
class BaseModel(models.Model):
    """
    Abstract base model that all models should inherit from.
    Provides common fields: is_active, is_deleted, created, updated
    Automatically orders by most recently updated first
    """
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    history = HistoricalRecords(inherit=True) 
    
    class Meta:
        abstract = True
        ordering = ['-updated', '-created']
        
        
    @property
    def content_type(self):
        """
        Get ContentType for this model instance.
        Returns the ContentType object for this model.
        """
        return ContentType.objects.get_for_model(self.__class__)
    

    
    def history_per_field(self, field_name: str) -> list[dict]:
        """
        Returns all history records where the specified field changed.
        
        Usage:
            employee.history_per_field("status")
            employee.history_per_field("email")
        """
        records = self.history.all()
        changes = []

        for i, record in enumerate(records):
            # No previous record to compare against (first ever record)
            if i + 1 >= len(records):
                break

            previous = records[i + 1]
            delta = record.diff_against(previous)

            for change in delta.changes:
                if change.field == field_name:
                    changes.append({
                        "history_id":     record.history_id,
                        "changed_on":     record.history_date,
                        "changed_by":     record.history_user,
                        "change_reason":  record.history_change_reason,
                        "field":          change.field,
                        "old_value":      change.old,
                        "new_value":      change.new,
                    })

        return changes

    def save_with_reason(self, reason: str, *args, **kwargs):
        """
        Shortcut to save with a history_change_reason.
        
        Usage:
            employee.save_with_reason("Status updated by manager")
        """
        self._change_reason = reason
        self.save(*args, **kwargs)
        
    @property
    def previous_status(self):
        """Get the status before the current one using simple history."""
        return (
            self.history
            .exclude(status=self.status)
            .order_by("-history_date")
            .values_list("status", flat=True)
            .first()
        )
        
    @can_export
    @property
    def created_by(self):
        first = self.history.order_by("history_date").first()
        return first.history_user if first else None