from django.contrib import admin
from .models import Rider, Driver, Ride, KeyValueConfig

admin.site.register(Rider)
admin.site.register(Driver)
admin.site.register(Ride)
admin.site.register(KeyValueConfig)
