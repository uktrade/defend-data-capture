from django import forms
from django.db.models import TextChoices
from django.forms.utils import ErrorList

from .widgets import (
    DetailSelectMixin,
    DetailRadioSelect,
    HintedDetailRadioSelect,
    DateMultiTextInputWidget,
)
from .models import StrategicActionUpdate, RAGRatingHints, StrategicAction


class DetailFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, key, config in self.detail_forms:
            try:
                form_class = config["form_class"]
                kwargs["prefix"] = key
                config["form"] = form_class(*args, **kwargs)
            except KeyError:
                pass

    def is_valid(self):
        # this should only be called for the option that's selected
        valid = super().is_valid()
        for field_name, key, config in self.detail_forms:
            if self.cleaned_data[field_name] == key:
                valid = config["form"].is_valid() and valid
        return valid

    def save(self, commit=True):
        for field_name, key, config in self.detail_forms:
            # no need to commit if the models are the same
            # as the outer form will do that below, if commit=True
            # N.B. this assumes inner forms are using the same instance
            # But sometimes they aren't…
            inner_commit = self.instance == config["form"].instance
            if self.cleaned_data[field_name] == key:
                config["form"].save(commit=inner_commit)
        return super().save(commit=commit)

    @property
    def detail_forms(self):
        for field_name, field in self.fields.items():
            if isinstance(field.widget, DetailSelectMixin):
                for key, config in field.widget.details.items():
                    yield (field_name, key, config)


class YesNoChoices(TextChoices):
    YES = (True, "Yes")
    NO = (False, "No")


class MonthlyUpdateInfoForm(forms.ModelForm):
    class Meta:
        model = StrategicActionUpdate
        fields = [
            "content",
        ]
        widgets = {
            "content": forms.Textarea(
                attrs={
                    "class": "govuk-textarea",
                }
            )
        }


class AmberReasonForDelayForm(forms.ModelForm):
    class Meta:
        model = StrategicActionUpdate
        fields = ["reason_for_delays"]
        labels = {"reason_for_delays": "Explain potential risk"}
        widgets = {
            "reason_for_delays": forms.Textarea(attrs={"class": "govuk-textarea"})
        }


class RedReasonForDelayForm(AmberReasonForDelayForm):

    will_completion_date_change = forms.ChoiceField(
        choices=YesNoChoices.choices,
        widget=forms.RadioSelect(attrs={"class": "govuk-radios__input"}),
        label="Will the estimated completion date change?",
    )

    class Meta(AmberReasonForDelayForm.Meta):
        labels = {"reason_for_delays": "Explain issue"}


class MonthlyUpdateStatusForm(DetailFormMixin, forms.ModelForm):
    class Meta:
        model = StrategicActionUpdate
        fields = ["implementation_rag_rating"]
        widgets = {
            "implementation_rag_rating": HintedDetailRadioSelect(
                attrs={
                    "class": "govuk-radios__input",
                    "data-aria-controls": "{id}-detail",
                },
                hints=RAGRatingHints,
                details={
                    "RED": {
                        "template": "supply_chains/includes/reason-for-delays.html",
                        "form_class": RedReasonForDelayForm,
                    },
                    "AMBER": {
                        "template": "supply_chains/includes/reason-for-delays.html",
                        "form_class": AmberReasonForDelayForm,
                    },
                },
            )
        }
        labels = {"implementation_rag_rating": "Current delivery status"}


class CompletionDateForm(forms.ModelForm):
    class Meta:
        model = StrategicAction
        fields = ["target_completion_date"]
        labels = {"target_completion_date": "Date for intended completion"}


class ApproximateTimings(TextChoices):
    THREE_MONTHS = ("3", "3 months")
    SIX_MONTHS = ("6", "6 months")
    ONE_YEAR = ("12", "1 year")
    TWO_YEARS = ("24", "2 years")
    ONGOING = ("0", "Ongoing")


class ApproximateTimingForm(forms.ModelForm):
    surrogate_is_ongoing = forms.ChoiceField(
        choices=ApproximateTimings.choices,
        label="What is the approximate time for completion?",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["surrogate_is_ongoing"].widget = forms.RadioSelect(
            choices=self.fields["surrogate_is_ongoing"].choices,
            attrs={
                "class": "govuk-radios__input",
            },
        )

    class Meta:
        model = StrategicAction
        fields = []
        labels = {
            "surrogate_is_ongoing": "What is the approximate time for completion?",
        }


class MonthlyUpdateTimingForm(DetailFormMixin, forms.ModelForm):
    is_completion_date_known = forms.ChoiceField(
        choices=YesNoChoices.choices,
        widget=DetailRadioSelect(
            attrs={"class": "govuk-radios__input", "data-aria-controls": "{id}-detail"},
            details={
                "True": {
                    "template": "supply_chains/includes/completion-date.html",
                    "form_class": CompletionDateForm,
                },
                "False": {
                    "template": "supply_chains/includes/approximate-timing.html",
                    "form_class": ApproximateTimingForm,
                },
            },
        ),
        label="Is there an expected completion date?",
    )

    class Meta:
        model = StrategicAction
        fields = []
