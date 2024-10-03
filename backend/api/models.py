"""Models for the api app."""
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class SatelliteAcqusition(models.Model):
    """Satellite acqusitions."""

    path = models.CharField(max_length=3)
    row = models.CharField(max_length=3)
    datetime = models.DateTimeField()
    satellite = models.CharField(max_length=20)


class AcqusitionDatesInfo(models.Model):
    """Acqusition dates info."""

    satellite = models.CharField(max_length=20)
    has_info_date = models.DateField()



class Reminder(models.Model):
    """
    Model representing a reminder.

    **Fields**:
    - `title`: CharField, required, the title of the reminder.
    - `description`: TextField, required, the detailed description
    of the reminder.
    - `due_date`: DateField, required, the date by which the reminder
    should be addressed.
    - `is_sent`: BooleanField, default=False, indicates whether the
    reminder has been sent.
    - `user`: ForeignKey, required, a reference to the User who created
    the reminder.
    """

    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField()
    is_sent = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        """Return a string representation of the Reminder object."""
        return self.title
