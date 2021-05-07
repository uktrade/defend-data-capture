from django.contrib import admin

from accounts.models import GovDepartment
from supply_chains.models import SupplyChain, StrategicAction, StrategicActionUpdate

admin.site.register(GovDepartment)
admin.site.register(SupplyChain)
admin.site.register(StrategicAction)
admin.site.register(StrategicActionUpdate)
