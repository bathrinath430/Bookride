from django.core.management.base import BaseCommand
from django.utils import timezone
import random
from datetime import timedelta
from core.models import Rider, Driver, Ride, KeyValueConfig
from core.services import try_assign_driver

class Command(BaseCommand):
    help = "Simulate 2 days of rides"

    def handle(self, *args, **kwargs):
        Rider.objects.all().delete()
        Driver.objects.all().delete()
        Ride.objects.all().delete()
        KeyValueConfig.objects.all().delete()
        # pricing config
        KeyValueConfig.objects.bulk_create([
            KeyValueConfig(key="base_fare", value=50),
            KeyValueConfig(key="rate_per_km", value=10),
            KeyValueConfig(key="rate_per_minute", value=1),
            KeyValueConfig(key="waiting_rate_per_minute", value=0.5),
        ])
        # generate riders & drivers
        for i in range(10):
            Rider.objects.create(name=f"Rider{i+1}", lat=12.9+random.uniform(-0.05,0.05), lng=77.6+random.uniform(-0.05,0.05))
        for i in range(15):
            Driver.objects.create(name=f"Driver{i+1}", lat=12.9+random.uniform(-0.05,0.05), lng=77.6+random.uniform(-0.05,0.05))
        start_time = timezone.now() - timedelta(days=2)
        for day in range(2):
            for rider in Rider.objects.all():
                for _ in range(random.randint(1,2)):
                    pickup_lat = rider.lat + random.uniform(-0.02,0.02)
                    pickup_lng = rider.lng + random.uniform(-0.02,0.02)
                    drop_lat = pickup_lat + random.uniform(-0.05,0.05)
                    drop_lng = pickup_lng + random.uniform(-0.05,0.05)
                    ride = Ride.objects.create(
                        rider=rider,
                        pickup_lat=pickup_lat,
                        pickup_lng=pickup_lng,
                        drop_lat=drop_lat,
                        drop_lng=drop_lng,
                        created_at=start_time + timedelta(days=day, minutes=random.randint(0, 1440))
                    )
                    try_assign_driver(ride)
        total_rides = Ride.objects.count()
        assigned_rides = Ride.objects.exclude(driver=None).count()
        print(f"Total rides: {total_rides}, Assigned: {assigned_rides}, Unassigned: {total_rides - assigned_rides}")
        for driver in Driver.objects.all():
            rides = Ride.objects.filter(driver=driver).count()
            earnings = sum(r.fare_total or 0 for r in Ride.objects.filter(driver=driver))
            print(f"{driver.name}: rides={rides}, earnings={earnings}")

