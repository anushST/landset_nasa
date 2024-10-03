"""Serializers of api app."""
from rest_framework import serializers
from .models import Reminder, SatelliteAcqusition


class SatelliteAcqusitionSerializer(serializers.ModelSerializer):

    class Meta:
        model = SatelliteAcqusition
        fields='__all__'


class ReminderSerializer(serializers.ModelSerializer):
    """Serializer for the Reminder model.

    This serializer handles the validation and serialization of
    Reminder instances, allowing for the creation and updating of
    reminders.

    **Fields**:
    - `id`: IntegerField, auto-generated ID of the reminder.
    - `title`: CharField, the title of the reminder (required).
    - `description`: TextField, the detailed description of the reminder
    (required).
    - `due_date`: DateField, the date by which the reminder should be
    addressed (required).
    - `is_sent`: BooleanField, indicates whether the reminder has been sent
    (default=False).
    """

    class Meta:
        """Meta-data of the ReminderSerializer class."""

        model = Reminder
        fields = ('id', 'title', 'description', 'due_date', 'is_sent',)
        read_only_fields = ('is_sent',)

    
class LandsatSearchSerializer(serializers.Serializer):
    time_range = serializers.CharField(
        help_text="Time range for the search in the format 'YYYY-MM-DD/YYYY-MM-DD'."
    )
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    min_cloud_cover = serializers.FloatField(min_value=0, max_value=100, required=False)
    max_cloud_cover = serializers.FloatField(min_value=0, max_value=100, required=False)
