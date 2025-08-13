from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
import random
from django.utils import timezone
from .models import Ride, Driver, KeyValueConfig
from .utils import haversine_km

AVG_SPEED_KMH = 40.0

def get_kv(key, default=0):
    try:
        return Decimal(str(KeyValueConfig.objects.get(key=key).value))
    except KeyValueConfig.DoesNotExist:
        return Decimal(str(default))

def driver_is_eligible(driver, ride):
    active = Ride.objects.filter(driver=driver, state__in=['driver_assigned','driver_at_location','start_ride']).exists()
    if active: return False
    recent_same = Ride.objects.filter(driver=driver, rider=ride.rider, end_at__gte=ride.created_at - timedelta(minutes=30), state='end_ride').exists()
    if recent_same: return False
    if driver.consecutive_cancellations >= 2: return False
    if driver.status != 'AVAILABLE': return False
    return True

def try_assign_driver(ride, max_radius_km=20):
    attempt = 0
    while True:
        radius_km = 2 * (attempt + 1)
        waited_seconds = attempt * 10
        candidates = []
        for d in Driver.objects.filter(status='AVAILABLE'):
            d_dist = haversine_km(d.lat, d.lng, ride.pickup_lat, ride.pickup_lng)
            if d_dist <= radius_km and driver_is_eligible(d, ride):
                candidates.append((d, d_dist))
        if candidates:
            candidates.sort(key=lambda x: x[1])
            driver, distance_to_pickup = candidates[0]
            ride.driver = driver
            ride.state = 'driver_assigned'
            ride.driver_assigned_at = ride.created_at + timedelta(seconds=waited_seconds)
            driver.status = 'ON_TRIP'
            driver.save()
            seconds_to_reach = int(distance_to_pickup / AVG_SPEED_KMH * 3600)
            ride.driver_at_location_at = ride.driver_assigned_at + timedelta(seconds=seconds_to_reach)
            ride.state = 'driver_at_location'
            rider_delay = random.randint(5, 120)
            ride.start_at = ride.driver_at_location_at + timedelta(seconds=rider_delay)
            ride.state = 'start_ride'
            ride.waiting_seconds = rider_delay
            trip_km = haversine_km(ride.pickup_lat, ride.pickup_lng, ride.drop_lat, ride.drop_lng)
            ride.distance_km = Decimal(str(round(trip_km, 3)))
            seconds_trip = int(trip_km / AVG_SPEED_KMH * 3600)
            ride.end_at = ride.start_at + timedelta(seconds=seconds_trip)
            ride.duration_min = round((seconds_trip / 60.0), 2)
            compute_and_set_fare(ride)
            ride.state = 'end_ride'
            ride.save()
            driver.lat, driver.lng = ride.drop_lat, ride.drop_lng
            driver.status = 'AVAILABLE'
            driver.consecutive_cancellations = 0
            driver.save()
            return True
        attempt += 1
        if radius_km >= max_radius_km:
            return False

def compute_and_set_fare(ride):
    base = get_kv('base_fare', 0)
    per_km = get_kv('rate_per_km', 0)
    per_min = get_kv('rate_per_minute', 0)
    waiting_rate_per_min = get_kv('waiting_rate_per_minute', 0)
    distance = Decimal(str(ride.distance_km or 0))
    duration_mins = Decimal(str(ride.duration_min or 0))
    waiting_mins = Decimal(str(round((ride.waiting_seconds or 0) / 60.0, 2)))
    fare = base + (distance * per_km) + (duration_mins * per_min) + (waiting_mins * waiting_rate_per_min)
    fare = fare.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    ride.fare_total = fare
    ride.save()
    return fare
