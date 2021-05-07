from datetime import date

from django.forms.widgets import RadioSelect, Textarea, MultiWidget, TextInput


class GDSRadioSelect(RadioSelect):
    def __init__(self, attrs=None, choices=()):
        if attrs is None:
            attrs = {}
        if "class" not in attrs.keys():
            attrs["class"] = "govuk-radios__input"
        super().__init__(attrs, choices)


class HintedFieldMixin:
    def __init__(self, hint=None, attrs=None, **kwargs):
        attrs = kwargs.get("attrs", {})
        super().__init__(**kwargs)
        self.hint = hint


class HintedSelectMixin:
    def __init__(self, hints=None, **kwargs):
        super().__init__(**kwargs)
        self.hints: dict = {} if hints is None else hints

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )
        if value in self.hints.keys():
            option["dit_hint"] = self.hints[value]
        return option


class DetailSelectMixin:
    def __init__(self, details=None, select_label=None, **kwargs):
        super().__init__(**kwargs)
        self.details = {} if details is None else details
        self.select_label = select_label

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )
        if value in self.details.keys():
            option["dit_detail"] = self.details[value]
            try:
                option["attrs"]["data-aria-controls"] = option["attrs"][
                    "data-aria-controls"
                ].format(**option["attrs"])
            except KeyError:
                pass
        else:
            try:
                option["attrs"].pop("data-aria-controls")
            except KeyError:
                pass
        return option

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["has_details"] = bool(self.details)
        if self.select_label:
            context["select_label"] = self.select_label
        return context


class HintedRadioSelect(HintedSelectMixin, RadioSelect):
    template_name = "supply_chains/forms/widgets/gds-radio-group.html"
    option_template_name = "supply_chains/forms/widgets/gds-radio-option.html"


class HintedDetailRadioSelect(DetailSelectMixin, HintedSelectMixin, RadioSelect):
    template_name = "supply_chains/forms/widgets/gds-radio-group.html"
    option_template_name = "supply_chains/forms/widgets/gds-radio-option.html"


class DetailRadioSelect(DetailSelectMixin, RadioSelect):
    template_name = "supply_chains/forms/widgets/gds-radio-group.html"
    option_template_name = "supply_chains/forms/widgets/gds-radio-option.html"


class DateMultiTextInputWidget(MultiWidget):
    template_name = "supply_chains/forms/widgets/gds-date-multiwidget.html"

    def __init__(self, attrs=None, hint=None, labels=None, legend=None):
        widgets = {
            "day": TextInput(
                attrs={
                    "class": "govuk-input govuk-date-input__input govuk-input--width-2"
                }
            ),
            "month": TextInput(
                attrs={
                    "class": "govuk-input govuk-date-input__input govuk-input--width-2"
                }
            ),
            "year": TextInput(
                attrs={
                    "class": "govuk-input govuk-date-input__input govuk-input--width-4"
                }
            ),
        }
        super().__init__(widgets, attrs)
        self.labels = labels
        self.govuk_hint = hint
        self.legend = legend

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if self.labels is not None:
            labelled_widgets = []
            for index, (field_name, label) in enumerate(self.labels.items()):
                labelled_widgets.append(
                    {
                        "field_name": field_name,
                        "label": label,
                        "widget": context["widget"]["subwidgets"][index],
                    }
                )
            context["labelled_widgets"] = labelled_widgets
        if self.govuk_hint is not None:
            context["hint"] = self.govuk_hint
        if self.legend is not None:
            context["legend"] = self.legend
        return context

    def decompress(self, value):
        if isinstance(value, date):
            return [value.day, value.month, value.year]
        if isinstance(value, str):
            year, month, day = value.split("-")
            return [day, month, year]
        return [None, None, None]

    def value_from_datadict(self, data, files, name):
        day, month, year = super().value_from_datadict(data, files, name)
        return f"{year}-{month}-{day}"
