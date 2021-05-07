from datetime import date, datetime, timedelta

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.template.defaultfilters import slugify
import reversion

from accounts.models import GovDepartment
import uuid
from .utils import get_last_working_day_of_previous_month


class RAGRating(models.TextChoices):
    RED = ("RED", "Red")
    AMBER = ("AMBER", "Amber")
    GREEN = ("GREEN", "Green")


RAGRatingHintsText = [
    "There is an issue with delivery of an action. This will require escalation and further support. There is a "
    "potential risk to the expected completion date.",
    "There's a potential risk to delivery that needs monitoring.",
    "Delivery is on track with no issues",
]

RAGRatingHints = {
    rating[0]: help_text
    for rating, help_text in zip(
        reversed(RAGRating.choices), reversed(RAGRatingHintsText)
    )
}


class SupplyChainQuerySet(models.QuerySet):
    def submitted_since(self, deadline):
        return self.filter(last_submission_date__gt=deadline)


class SupplyChain(models.Model):
    class StatusRating(models.TextChoices):
        LOW = ("low", "Low")
        MEDIUM = ("medium", "Medium")
        HIGH = ("high", "High")

    objects = SupplyChainQuerySet.as_manager()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=settings.CHARFIELD_MAX_LENGTH)
    last_submission_date = models.DateField(null=True)
    gov_department = models.ForeignKey(
        GovDepartment,
        on_delete=models.PROTECT,
        related_name="supply_chains",
    )
    contact_name = models.CharField(max_length=settings.CHARFIELD_MAX_LENGTH)
    contact_email = models.CharField(max_length=settings.CHARFIELD_MAX_LENGTH)
    vulnerability_status = models.CharField(
        choices=StatusRating.choices,
        max_length=6,
    )
    vulnerability_status_disagree_reason = models.TextField(blank=True)
    risk_severity_status = models.CharField(
        choices=StatusRating.choices,
        max_length=6,
    )
    risk_severity_status_disagree_reason = models.TextField(blank=True)
    slug = models.SlugField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    archived_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if self.is_archived and self.archived_date is None:
            self.archived_date = timezone.now().date()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"SC: {self.name}, {self.gov_department.name}"


@reversion.register()
class StrategicAction(models.Model):
    class Category(models.TextChoices):
        CREATE = ("create", "Create")
        DIVERSIFY = ("diversify", "Diversify")
        EXPAND = ("expand", "Expand")
        PARTNER = ("partner", "Partner")

    class GeographicScope(models.TextChoices):
        UK_WIDE = ("uk_wide", "UK-wide")
        ENGLAND_ONLY = ("england_only", "England only")

    class SupportingOrgs(models.TextChoices):
        HMT = ("HMT", "Treasury")
        DHSC = ("DHSC", "DHSC")
        BEIS = ("BEIS", "BEIS")
        DCMS = ("DCMS", "DCMS")
        DIT = ("DIT", "DIT")
        DEFRA = ("DEFRA", "DEFRA")
        CABINET_OFFICE = ("CABINET_OFFICE", "Cabinet Office")
        MOD = ("MOD", "MoD")
        HOME_OFFICE = ("HOME_OFFICE", "Home Office")
        FCDO = ("FCDO", "FCDO")
        DEVOLVED_ADMINISTRATIONS = (
            "DEVOLVED_ADMINISTRATIONS",
            "Devolved administrations",
        )
        DFT = ("DFT", "DfT")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=settings.CHARFIELD_MAX_LENGTH)
    start_date = models.DateField()
    description = models.TextField()
    impact = models.TextField()
    category = models.CharField(
        choices=Category.choices,
        max_length=9,
    )
    geographic_scope = models.CharField(
        choices=GeographicScope.choices,
        max_length=12,
    )
    supporting_organisations = models.CharField(
        max_length=24, choices=SupportingOrgs.choices, blank=True
    )
    is_ongoing = models.BooleanField(default=False)
    target_completion_date = models.DateField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    archived_date = models.DateField(null=True, blank=True)
    archived_reason = models.TextField(blank=True)
    specific_related_products = models.TextField(
        help_text="Details of specific products within the supply chain which the action applies to, if applicable.",
        blank=True,
    )
    other_dependencies = models.TextField(
        help_text="Any other dependencies or requirements for completing the action.",
        blank=True,
    )
    supply_chain = models.ForeignKey(
        SupplyChain,
        on_delete=models.PROTECT,
        related_name="strategic_actions",
    )
    slug = models.SlugField(null=True, blank=True)

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        if self.is_archived and self.archived_reason == "":
            raise ValidationError(
                "An archived_reason must be given when archiving a strategic action."
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if self.is_archived and not self.archived_date:
            self.archived_date = timezone.now().date()
        self.full_clean()
        return super().save(*args, **kwargs)

    def last_submitted_update(self):
        return self.monthly_updates.last_month()

    def __str__(self):
        return f"SA: {self.name}, {self.supply_chain.gov_department.name}, {self.get_geographic_scope_display()}, SC: {self.supply_chain.name}"


class SAUQuerySet(models.QuerySet):
    def since(self, deadline, *args, **kwargs):
        return self.filter(date_created__gt=deadline, *args, **kwargs)

    def last_month(self, before_date=None):
        if before_date is None:
            before_date = datetime.now().date()
        last_month_deadline = get_last_working_day_of_previous_month()
        return (
            self.filter(submission_date__lte=last_month_deadline)
            .order_by("-submission_date")
            .first()
        )


class StrategicActionUpdate(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = ("not_started", "Not started")
        IN_PROGRESS = ("in_progress", "In progress")
        COMPLETED = ("completed", "Completed")
        SUBMITTED = ("submitted", "Submitted")

    objects = SAUQuerySet.as_manager()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(
        max_length=11,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
        help_text="""The 'completed' and 'in_progress' statuses are used to help
 users know whether they have completed all required fields for an update.
 The 'submitted' status refers to when a user can no longer edit an update.""",
    )
    submission_date = models.DateField(null=True, blank=True)
    date_created = models.DateField(auto_now_add=True)
    content = models.TextField(blank=True)
    implementation_rag_rating = models.CharField(
        max_length=5,
        choices=reversed(RAGRating.choices),
        blank=True,
        default=None,
        null=True,
    )
    reason_for_delays = models.TextField(blank=True)
    changed_target_completion_date = models.DateField(null=True, blank=True)
    reason_for_completion_date_change = models.TextField(blank=True)
    changed_is_ongoing = models.BooleanField(null=True, default=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="monthly_updates",
    )
    strategic_action = models.ForeignKey(
        StrategicAction,
        on_delete=models.PROTECT,
        related_name="monthly_updates",
    )
    supply_chain = models.ForeignKey(
        SupplyChain,
        on_delete=models.PROTECT,
        related_name="monthly_updates",
    )
    slug = models.SlugField(null=True, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.slug:
            self.slug = self.date_created.strftime("%m-%Y")
            try:
                kwargs.pop("force_insert")
            except KeyError:
                pass
            self.save(*args, **kwargs)

    def __str__(self):
        return f"SAU: {self.strategic_action.name}, {self.slug}, {self.get_status_display()}"

    def some_completion_date(self):
        if self.strategic_action.target_completion_date is not None:
            return self.strategic_action.target_completion_date
        if self.changed_target_completion_date is not None:
            return self.changed_target_completion_date
        return None

    @property
    def has_existing_target_completion_date(self):
        return self.strategic_action.target_completion_date is not None

    @property
    def has_changed_target_completion_date(self):
        return self.changed_target_completion_date is not None

    @property
    def has_updated_target_completion_date(self):
        return (
            self.changed_target_completion_date is not None
            and self.has_existing_target_completion_date
        )

    @property
    def has_new_target_completion_date(self):
        return (
            self.changed_target_completion_date is not None
            and not self.has_existing_target_completion_date
        )

    @property
    def has_no_target_completion_date(self):
        return (
            not self.has_changed_target_completion_date
            and not self.has_existing_target_completion_date
        )

    @property
    def is_currently_ongoing(self):
        return self.strategic_action.is_ongoing

    @property
    def is_becoming_ongoing(self):
        return self.changed_is_ongoing

    @property
    def has_no_is_ongoing(self):
        return not self.is_currently_ongoing and not self.is_becoming_ongoing

    @property
    def is_changing_is_ongoing(self):
        return self.is_becoming_ongoing and (
            self.is_currently_ongoing or self.has_existing_target_completion_date
        )

    @property
    def has_new_is_ongoing(self):
        return self.is_becoming_ongoing and not (
            self.is_currently_ongoing or self.has_existing_target_completion_date
        )

    @property
    def is_changing_target_completion_date(self):
        return self.has_updated_target_completion_date or self.is_changing_is_ongoing

    @property
    def has_no_timing_information(self):
        return self.has_no_target_completion_date and self.has_no_is_ongoing


class MaturitySelfAssessment(models.Model):
    class RatingLevel(models.TextChoices):
        LEVEL_1 = ("level_1", "Level 1")
        LEVEL_2 = ("level_2", "Level 2")
        LEVEL_3 = ("level_3", "Level 3")
        LEVEL_4 = ("level_4", "Level 4")
        LEVEL_5 = ("level_5", "Level 5")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_created = models.DateField(auto_now_add=True)
    maturity_rating_reason = models.TextField()
    maturity_rating_level = models.CharField(
        choices=RatingLevel.choices,
        max_length=7,
    )
    supply_chain = models.ForeignKey(
        SupplyChain,
        on_delete=models.PROTECT,
        related_name="maturity_self_assessment",
    )


class VulnerabilityAssessment(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_created = models.DateField(auto_now_add=True)
    supply_rag_rating = models.CharField(
        max_length=5,
        choices=RAGRating.choices,
    )
    supply_rating_reason = models.TextField(
        help_text="""This field collects information about the characteristics that
        contribute to the vulnerability of the supply element of the chain.""",
    )
    make_rag_rating = models.CharField(
        max_length=5,
        choices=RAGRating.choices,
    )
    make_rating_reason = models.TextField(
        help_text="""This field collects information about the characteristics that
        contribute to the vulnerability of the make element of the chain.""",
    )
    receive_rag_rating = models.CharField(
        max_length=5,
        choices=RAGRating.choices,
    )
    receive_rating_reason = models.TextField(
        help_text="""This field collects information about the characteristics that
        contribute to the vulnerability of the receive element of the chain.""",
    )
    store_rag_rating = models.CharField(
        max_length=5,
        choices=RAGRating.choices,
    )
    store_rating_reason = models.TextField(
        help_text="""This field collects information about the characteristics that
        contribute to the vulnerability of the store element of the chain.""",
    )
    deliver_rag_rating = models.CharField(
        max_length=5,
        choices=RAGRating.choices,
    )
    deliver_rating_reason = models.TextField(
        help_text="""This field collects information about the characteristics that
        contribute to the vulnerability of the deliver element of the chain.""",
    )
    supply_chain = models.ForeignKey(
        SupplyChain,
        on_delete=models.PROTECT,
        related_name="vulnerability_assessment",
    )


class ScenarioAssessment(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_created = models.DateField(auto_now_add=True)
    borders_closed_impact = models.TextField(
        help_text="""This field collects information about the potential impacts that would occur should
        the borders close.""",
    )
    borders_closed_rag_rating = models.CharField(
        max_length=5,
        choices=RAGRating.choices,
    )
    storage_full_impact = models.TextField(
        help_text="""This field collects information about the potential impacts that would occur should
        storage facilities be full.""",
    )
    storage_full_rag_rating = models.CharField(
        max_length=5,
        choices=RAGRating.choices,
    )
    ports_blocked_impact = models.TextField(
        help_text="""This field collects information about the potential impacts that would occur should
        the ports be blocked.""",
    )
    ports_blocked_rag_rating = models.CharField(
        max_length=5,
        choices=RAGRating.choices,
    )
    raw_material_shortage_impact = models.TextField(
        help_text="""This field collects information about the potential impacts that would occur should
        there be a raw material shortage.""",
    )
    raw_material_shortage_rag_rating = models.CharField(
        max_length=5,
        choices=RAGRating.choices,
    )
    labour_shortage_impact = models.TextField(
        help_text="""This field collects information about the potential impacts that would occur should
        there be a labour shortage.""",
    )
    labour_shortage_rag_rating = models.CharField(
        max_length=5,
        choices=RAGRating.choices,
    )
    demand_spike_impact = models.TextField(
        help_text="""This field collects information about the potential impacts that would occur should
        the demand spike.""",
    )
    demand_spike_rag_rating = models.CharField(
        max_length=5,
        choices=RAGRating.choices,
    )
    supply_chain = models.ForeignKey(
        SupplyChain,
        on_delete=models.PROTECT,
        related_name="scenario_assessment",
    )
