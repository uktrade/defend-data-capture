from import_export import resources
from accounts.models import User, GovDepartment
from supply_chains.models import (
    StrategicAction,
    StrategicActionUpdate,
    SupplyChain,
    MaturitySelfAssessment,
    VulnerabilityAssessment,
    ScenarioAssessment,
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


class SupplyChainResource(resources.ModelResource):
    class Meta:
        model = SupplyChain


class MaturitySelfAssessmentResource(resources.ModelResource):
    class Meta:
        model = MaturitySelfAssessment


class ScenarioAssessmentResource(resources.ModelResource):
    class Meta:
        model = ScenarioAssessment


class VulnerabilityAssessmentResource(resources.ModelResource):
    class Meta:
        model = VulnerabilityAssessment
