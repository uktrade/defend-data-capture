import calendar
from datetime import date, datetime, timedelta

import holidays


def get_last_working_day_of_a_month(last_day_of_month: date) -> date:
    """
    When provided with a date object representing the last day of a month,
    this function will return the last working day of that month.
    """
    uk_holidays = holidays.UnitedKingdom()
    if last_day_of_month in uk_holidays or last_day_of_month.weekday() > 4:
        return get_last_working_day_of_a_month(last_day_of_month - timedelta(days=1))
    else:
        return last_day_of_month


def get_last_day_of_this_month() -> date:
    """Returns the last day of the current month"""
    today = datetime.today()
    return date(
        today.year, today.month, calendar.monthrange(today.year, today.month)[1]
    )


def get_last_working_day_of_previous_month() -> date:
    """
    Returns the last working day of the previous month.
    """
    last_day_of_previous_month = date.today().replace(day=1) - timedelta(1)
    previous_month_deadline = get_last_working_day_of_a_month(
        last_day_of_previous_month
    )
    return previous_month_deadline
