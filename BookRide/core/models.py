from django.db import models
from django.utils import timezone
from decimal import Decimal

class KeyValueConfig(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.DecimalField(max_digits=12, decimal_places=4)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.key}={self.value}"

class Rider(models.Model):
    name = models.CharField(max_length=100)
    lat = models.FloatField()
    lng = models.FloatField()
    def __str__(self):
        return self.name

class Driver(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('ON_TRIP', 'On trip'),
        ('OFFLINE', 'Offline'),
    ]
    name = models.CharField(max_length=100)
    lat = models.FloatField()
    lng = models.FloatField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    consecutive_cancellations = models.IntegerField(default=0)
    def __str__(self):
        return f"{self.name} ({self.status})"

class Ride(models.Model):
    STATE_CHOICES = [
        ('create_ride', 'create_ride'),
        ('driver_assigned', 'driver_assigned'),
        ('driver_at_location', 'driver_at_location'),
        ('start_ride', 'start_ride'),
        ('end_ride', 'end_ride'),
        ('cancelled', 'cancelled'),
    ]
    rider = models.ForeignKey(Rider, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    pickup_lat = models.FloatField()
    pickup_lng = models.FloatField()
    drop_lat = models.FloatField()
    drop_lng = models.FloatField()
    state = models.CharField(max_length=30, choices=STATE_CHOICES, default='create_ride')
    created_at = models.DateTimeField(default=timezone.now)
    driver_assigned_at = models.DateTimeField(null=True, blank=True)
    driver_at_location_at = models.DateTimeField(null=True, blank=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    distance_km = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    duration_min = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    waiting_seconds = models.IntegerField(null=True, blank=True)
    fare_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cancelled_by = models.CharField(max_length=20, null=True, blank=True)
    def __str__(self):
        return f"Ride {self.pk} {self.state} rider={self.rider}"
