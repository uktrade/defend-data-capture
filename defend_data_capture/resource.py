from import_export import resources
from accounts.models import User, GovDepartment
from supply_chains.models import (
    StrategicAction,
    StrategicActionUpdate,
    SupplyChain,
)


class UserResource(resources.ModelResource):
    class Meta:
        model = User


class GovDepartmentResource(resources.ModelResource):
    class Meta:
        model = GovDepartment


class StrategicActionResource(resources.ModelResource):
    class Meta:
        model = StrategicAction


class StrategicActionUpdateResource(resources.ModelResource):
    class Meta:
        model = StrategicActionUpdate


class SupplyChainUpdateResource(resources.ModelResource):
    class Meta:
        model = SupplyChain
