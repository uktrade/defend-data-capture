from datetime import date

from dateutil.relativedelta import relativedelta
from django import forms
from django.db.models import TextChoices
from django.forms.utils import ErrorDict

from .widgets import (
    DetailSelectMixin,
    DetailRadioSelect,
    HintedDetailRadioSelect,
    DateMultiTextInputWidget,
)
from .models import StrategicActionUpdate, RAGRatingHints, StrategicAction, RAGRating


class MakeFieldRequiredMixin:
    field_to_make_required = None

    def make_field_required(self):
        if self.field_to_make_required is not None:
            self.fields[self.field_to_make_required].required = True

    def make_field_not_required(self):
        if self.field_to_make_required is not None:
            self.fields[self.field_to_make_required].required = False


class DetailFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._detail_forms_dict = {}
        for field_name, key, config in self.detail_forms:
            try:
                form_class = config["form_class"]
                kwargs["prefix"] = key
                config["form"] = form_class(*args, **kwargs)
                self._detail_forms_dict[key] = config["form"]
            except KeyError:
                pass

    def detail_form_for_key(self, key):
        try:
            return self._detail_forms_dict[key]
        except KeyError:
            return None

    def is_valid(self):
        # this should only be called for the option that's selected
        valid = super().is_valid()
        for field_name, key, config in self.detail_forms:
            if (
                field_name in self.cleaned_data.keys()
                and self.cleaned_data[field_name] == key
            ):
                valid = all(
                    (
                        config["form"].is_valid(),
                        valid,
                    )
                )
        return valid

    def save(self, commit=True):
        for field_name, key, config in self.detail_forms:
            # no need to commit if the instances are the same
            # as the outer form will do that below (if commit=True)
            # N.B. this assumes inner forms are using the same instance
            # But sometimes maybe they aren't… best check for it
            # If they aren't, we need to commit iff commit=True
            inner_commit = all(
                (
                    self.instance != config["form"].instance,
                    commit,
                )
            )
            if self.cleaned_data[field_name] == key:
                config["form"].save(commit=inner_commit)
        return super().save(commit=commit)

    @property
    def detail_forms(self):
        for field_name, field in self.fields.items():
            if isinstance(field.widget, DetailSelectMixin):
                for key, config in field.widget.details.items():
                    yield (field_name, key, config)

    class DetailFormErrors:
        def __get__(self, instance, owner):
            if instance is not None:
                return instance._errors
            else:
                return self._errors


class YesNoChoices(TextChoices):
    YES = ("True", "Yes")
    NO = ("False", "No")


class MonthlyUpdateInfoForm(forms.ModelForm):
    use_required_attribute = False
    content = forms.CharField(
        required=True,
        error_messages={"required": "Enter details of the latest monthly update."},
        widget=forms.Textarea(
            attrs={
                "class": "govuk-textarea",
                "novalidate": True,
            }
        ),
    )

    def is_valid(self):
        is_valid = super().is_valid()
        return is_valid

    class Meta:
        model = StrategicActionUpdate
        fields = [
            "content",
        ]


class AmberReasonForDelayForm(MakeFieldRequiredMixin, forms.ModelForm):
    use_required_attribute = False
    field_to_make_required = "reason_for_delays"

    def clean(self):
        cleaned = super().clean()
        return cleaned

    class Meta:
        model = StrategicActionUpdate
        fields = ["reason_for_delays"]
        labels = {"reason_for_delays": "Explain potential risk"}
        widgets = {
            "reason_for_delays": forms.Textarea(
                attrs={
                    "class": "govuk-textarea",
                    "novalidate": True,
                }
            )
        }


class RedReasonForDelayForm(AmberReasonForDelayForm):
    use_required_attribute = False
    will_completion_date_change = forms.ChoiceField(
        choices=YesNoChoices.choices,
        widget=forms.RadioSelect(
            attrs={
                "class": "govuk-radios__input",
                "novalidate": True,
            }
        ),
        label="Will the estimated completion date change?",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        strategic_action_update: StrategicActionUpdate = kwargs.get("instance", None)
        if strategic_action_update is not None:
            strategic_action: StrategicAction = strategic_action_update.strategic_action
            if strategic_action is not None:
                if (
                    strategic_action.target_completion_date is None
                    or strategic_action.is_ongoing
                ):
                    del self.fields["will_completion_date_change"]

    class Meta(AmberReasonForDelayForm.Meta):
        labels = {"reason_for_delays": "Explain issue"}


class MonthlyUpdateStatusForm(DetailFormMixin, forms.ModelForm):
    use_required_attribute = False
    implementation_rag_rating = forms.ChoiceField(
        required=True,
        choices=reversed(RAGRating.choices),
        label="Current delivery status",
        widget=HintedDetailRadioSelect(
            attrs={
                "class": "govuk-radios__input",
                "data-aria-controls": "{id}-detail",
                "novalidate": True,
            },
            hints=RAGRatingHints,
            details={
                RAGRating.RED: {
                    "template": "supply_chains/includes/reason-for-delays.html",
                    "form_class": RedReasonForDelayForm,
                },
                RAGRating.AMBER: {
                    "template": "supply_chains/includes/reason-for-delays.html",
                    "form_class": AmberReasonForDelayForm,
                },
            },
        ),
        error_messages={"required": "Select an option for the current delivery status"},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        strategic_action_update: StrategicActionUpdate = kwargs.get("instance", None)
        if strategic_action_update is not None:
            strategic_action: StrategicAction = strategic_action_update.strategic_action
            if strategic_action is not None:
                if (
                    strategic_action_update.strategic_action.target_completion_date
                    is None
                ):
                    red_reason_for_delay_form = self.detail_form_for_key(RAGRating.RED)
                    if (
                        "will_completion_date_change"
                        in red_reason_for_delay_form.fields.keys()
                    ):
                        will_completion_date_change_field = (
                            red_reason_for_delay_form.fields[
                                "will_completion_date_change"
                            ]
                        )
                        will_completion_date_change_field.required = False

    def is_valid(self):
        if "implementation_rag_rating" in self.data.keys():
            implementation_rag_rating = self.data["implementation_rag_rating"]
            required_form = self.detail_form_for_key(implementation_rag_rating)
            if required_form is not None:
                # we need the detail form field to be required for validation,
                # but not on the client as then they can't change their minds…
                required_form.make_field_required()
                required_form_is_valid = required_form.is_valid()
                required_form.make_field_not_required()
                form_is_valid = super().is_valid()
                # now ensure that any errors on the contained forms are also on the containing form
                if self._errors is None:
                    self._errors = ErrorDict()
                if required_form.errors is not None:
                    for field, error in required_form.errors.items():
                        self._errors[f"{required_form.prefix}-{field}"] = error
                return all(
                    (
                        form_is_valid,
                        required_form_is_valid,
                    )
                )
        return super().is_valid()

    def save(self, commit=True):
        instance: StrategicActionUpdate = self.instance
        if instance.implementation_rag_rating == RAGRating.RED:
            if instance.strategic_action.target_completion_date is not None:
                red_form = self.detail_form_for_key(RAGRating.RED)
                if (
                    red_form.cleaned_data["will_completion_date_change"]
                    == YesNoChoices.NO
                ):
                    # clear the values from the instance
                    instance.reason_for_completion_date_change = ""
                    instance.changed_target_completion_date = None
        return super().save(commit)

    class Meta:
        model = StrategicActionUpdate
        fields = ["implementation_rag_rating"]


class CompletionDateForm(MakeFieldRequiredMixin, forms.ModelForm):
    use_required_attribute = False
    field_to_make_required = "changed_target_completion_date"
    changed_target_completion_date = forms.DateField(
        widget=DateMultiTextInputWidget(
            attrs={
                "novalidate": True,
            },
            hint="For example 14 11 2021",
            labels={
                "day": "Day",
                "month": "Month",
                "year": "Year",
            },
            legend="Date for intended completion",
        ),
        label="Date for intended completion",
        required=False,
        input_formats=["%Y-%m-%d"],
        error_messages={
            "required": "Enter a date for intended completion",
            "invalid": "Enter a date for intended completion in the correct format",
        },
    )

    def save(self, commit=True):
        if "changed_target_completion_date" in self.cleaned_data.keys():
            self.instance.changed_is_ongoing = False
        return super().save(commit)

    class Meta:
        model = StrategicActionUpdate
        fields = ["changed_target_completion_date"]


class ApproximateTimings(TextChoices):
    THREE_MONTHS = ("3", "3 months")
    SIX_MONTHS = ("6", "6 months")
    ONE_YEAR = ("12", "1 year")
    TWO_YEARS = ("24", "2 years")
    ONGOING = ("0", "Ongoing")


class ApproximateTimingForm(MakeFieldRequiredMixin, forms.ModelForm):
    use_required_attribute = False
    surrogate_is_ongoing = forms.ChoiceField(
        choices=ApproximateTimings.choices,
        label="What is the approximate time for completion?",
        required=False,
    )
    field_to_make_required = "surrogate_is_ongoing"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["surrogate_is_ongoing"].widget = forms.RadioSelect(
            choices=self.fields["surrogate_is_ongoing"].choices,
            attrs={
                "class": "govuk-radios__input",
                "novalidate": True,
            },
        )

    def get_initial_for_field(self, field, field_name):
        if field_name == "surrogate_is_ongoing":
            if self.instance.changed_is_ongoing:
                return ApproximateTimings.ONGOING
        return super().get_initial_for_field(field, field_name)

    def save(self, commit=True):
        submitted_value = self.cleaned_data["surrogate_is_ongoing"]
        # As this form's field doesn't really exist…
        if submitted_value == ApproximateTimings["ONGOING"]:
            # we need to either set changed_is_ongoing and clear the completion date…
            self.instance.changed_is_ongoing = True
            self.instance.changed_target_completion_date = None
            self.instance.reason_for_completion_date_change = ""
        else:
            # or clear changed_is_ongoing and calculate the new completion date.
            self.instance.changed_is_ongoing = False
            months_hence = int(submitted_value)
            self.instance.changed_target_completion_date = date.today() + relativedelta(
                months=+months_hence
            )
        return super().save(commit)

    class Meta:
        model = StrategicActionUpdate
        fields = []
        labels = {
            "surrogate_is_ongoing": "What is the approximate time for completion?",
        }


class MonthlyUpdateTimingForm(DetailFormMixin, forms.ModelForm):
    use_required_attribute = False
    is_completion_date_known = forms.ChoiceField(
        required=True,
        choices=YesNoChoices.choices,
        label="Is there an expected completion date?",
        widget=DetailRadioSelect(
            attrs={
                "class": "govuk-radios__input",
                "data-aria-controls": "{id}-detail",
                "novalidate": True,
            },
            details={
                YesNoChoices.YES: {
                    "template": "supply_chains/includes/completion-date.html",
                    "form_class": CompletionDateForm,
                },
                YesNoChoices.NO: {
                    "template": "supply_chains/includes/approximate-timing.html",
                    "form_class": ApproximateTimingForm,
                },
            },
        ),
    )

    def get_initial_for_field(self, field, field_name):
        if field_name == "is_completion_date_known":
            detail_form = self.detail_form_for_key(YesNoChoices.NO)
            if detail_form.instance.changed_is_ongoing:
                return YesNoChoices.NO
            if detail_form.instance.changed_target_completion_date is not None:
                return YesNoChoices.YES
        return super().get_initial_for_field(field, field_name)

    def is_valid(self):
        # need to make one of the detail forms required, depending on our value
        if "is_completion_date_known" in self.data.keys():
            is_completion_date_known = self.data["is_completion_date_known"]
            required_form = self.detail_form_for_key(is_completion_date_known)
            if required_form is not None:
                form_is_valid = super().is_valid()
                # we need the detail form field to be required for validation,
                # but not on the client as then they can't change their minds…
                required_form.make_field_required()
                required_form_is_valid = required_form.is_valid()
                required_form.make_field_not_required()
                # now ensure that any errors on the contained forms are also on the containing form
                if self._errors is None:
                    self._errors = ErrorDict()
                if required_form.errors is not None:
                    for field, error in required_form.errors.items():
                        self._errors[f"{required_form.prefix}-{field}"] = error
                return all(
                    (
                        form_is_valid,
                        required_form_is_valid,
                    )
                )
        return super().is_valid()

    class Meta:
        model = StrategicActionUpdate
        fields = []
        labels = {"is_completion_date_known": "Is there an expected completion date?"}


class MonthlyUpdateModifiedTimingForm(MonthlyUpdateTimingForm):
    use_required_attribute = False
    reason_for_completion_date_change = forms.CharField(required=True)

    class Meta(MonthlyUpdateTimingForm.Meta):
        fields = MonthlyUpdateTimingForm.Meta.fields + [
            "reason_for_completion_date_change",
        ]


class MonthlyUpdateSubmissionForm:
    """ Not actually a form, this wraps the necessary forms and delegates to them """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__()
        strategic_action_update: StrategicActionUpdate = kwargs.get("instance", None)
        form_data = kwargs.get("data", None)
        if strategic_action_update is None:
            raise ValueError("No StrategicActionUpdate passed")
        self.instance = strategic_action_update
        self.forms = {}
        self.form_classes = (
            MonthlyUpdateInfoForm,
            MonthlyUpdateStatusForm,
        )
        strategic_action: StrategicAction = strategic_action_update.strategic_action
        timing_form_class = ()
        if strategic_action.target_completion_date is not None:
            if (
                strategic_action_update.changed_target_completion_date is not None
                or strategic_action_update.changed_is_ongoing
            ):
                timing_form_class += (MonthlyUpdateModifiedTimingForm,)
        else:
            timing_form_class += (MonthlyUpdateTimingForm,)
        if form_data is not None:
            # data will override the decisions we just made…
            timing_form_class = ()
            if (
                "changed_target_completion_date" in form_data.keys()
                or "surrogate_is_ongoing" in form_data.keys()
            ):
                if strategic_action.target_completion_date is not None:
                    # this is a change to an existing date
                    timing_form_class += (MonthlyUpdateModifiedTimingForm,)
                else:
                    timing_form_class += (MonthlyUpdateTimingForm,)
        self.form_classes += timing_form_class
        for form_class in self.form_classes:
            form = form_class(*args, **kwargs)
            self.forms[form_class.__name__] = form

    def is_valid(self):
        is_valid = []
        for form_class, form in self.forms.items():
            is_valid.append(form.is_valid())
        return all(is_valid)

    def save(self, *args, **kwargs):
        instance = None
        for form_class, form in self.forms.items():
            # This assumes all forms use the same model instance, which is true for this app
            instance = form.save(*args, **kwargs)
        self.instance = instance
        return self.instance

    @property
    def errors(self):
        errors = ErrorDict()
        for form_class, form in self.forms.items():
            errors.update(form.errors)
        return errors


# class MonthlyUpdateSubmissionForm2(forms.ModelForm):
#     class Meta:
#         model = StrategicActionUpdate
#         error_messages = {}
