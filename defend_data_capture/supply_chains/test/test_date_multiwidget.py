from supply_chains.widgets import date

import pytest

from django import forms
from django.core.exceptions import ValidationError
from supply_chains.widgets import DateMultiTextInputWidget


class TestDateMultiTextInputWidget:
    def test_widget_accepts_date_as_value(self):
        expected_year, expected_month, expected_date = (2020, 1, 31)
        date_value = date(expected_year, expected_month, expected_date)
        widget = DateMultiTextInputWidget()
        values = widget.decompress(date_value)
        assert 3 == len(values)
        assert expected_date == values[0]
        assert expected_month == values[1]
        assert expected_year == values[2]
        # widget_context = widget.get_context(name='test', value=date(2020, 1, 31), attrs={})

    def test_widget_returns_correctly_formatted_date_string_from_form_data(self):
        form_data = {"test_day": "31", "test_month": "01", "test_year": "2020"}
        expected_date_string = f'{form_data["test_year"]}-{form_data["test_month"]}-{form_data["test_day"]}'
        widget = DateMultiTextInputWidget()
        date_string = widget.value_from_datadict(form_data, files=None, name="test")
        assert expected_date_string == date_string

    def test_widget_has_subwidgets(self):
        widget = DateMultiTextInputWidget()
        assert hasattr(widget, "subwidgets")
        assert 3 == len(widget.widgets)

    def test_widget_hint(self):
        hint_text = "Test hint"
        widget = DateMultiTextInputWidget(hint=hint_text)
        assert hint_text == widget.govuk_hint
