from enum import Enum
from datetime import date


class Facility:
    def __init__(self, production_amount=0, taoz_cost=None, secondary_taoz_cost=None, se_per_hour=None,
                 number_of_pumps=None, water_cubic_meter_price=None, kwh_energy_limit=None):
        self.production_amount: int = production_amount
        self.taoz_cost: float = taoz_cost
        self.secondary_taoz_cost: float = secondary_taoz_cost
        self.se_per_hour: float = se_per_hour
        self.number_of_pumps: int = number_of_pumps
        self.water_cubic_meter_price: float = water_cubic_meter_price
        self.kwh_energy_limit: int = kwh_energy_limit
        self.shutdown: bool = False
        self.production_price: float = 0.0

    def calculate_price(self) -> None:
        """Calculates the production_price for the using facility."""
        if self.shutdown is False:
            self.production_price = self.se_per_hour * self.production_amount * self.taoz_cost


class MatrixBullet:
    def __init__(self, taoz=None, init_date=None, price=None):
        self.north_facility = Facility()
        self.south_facility = Facility()
        self.taoz: Taoz = taoz
        self.date: date = init_date
        self.price: float = price

    def calculate_price(self) -> None:
        """
        calculates the price for each facility and sum will be initialized in MatrixBullet,
        calculates the price in agurot.
        """
        self.north_facility.calculate_price()
        self.south_facility.calculate_price()
        self.price = self.north_facility.production_price + self.south_facility.production_price

    def define_taoz(self, taoz: str) -> None:
        """Initialize the taoz property to either 'SHEFEL', 'GEVA', 'PISGA'."""
        taoz_to_assign = None
        if taoz == 'SHEFEL':
            taoz_to_assign = Taoz.SHEFEL
        elif taoz == 'GEVA':
            taoz_to_assign = Taoz.GEVA
        else:
            taoz_to_assign = Taoz.PISGA

        self.taoz = taoz_to_assign

    def get_week_day(self) -> int:
        """Return day of the week, where Monday == 0 ... Sunday == 6."""
        return self.date.weekday()

    def get_season(self) -> str:
        """Return the season of the bullet, 'summer', 'winter' or 'spring_autumn'."""
        month = self.date.month
        if month == 7 or month == 8:
            return 'summer'
        elif month == 1 or month == 2 or month == 12:
            return 'winter'
        else:
            return 'spring_autumn'

    def get_day_representation(self) -> str:
        """
        Return the day representation of the bullet,
        'weekdays', 'friday_holiday_evening' or 'saturday_holiday'.
        """
        day = self.date.isoweekday()
        if day == 7 or 1 <= day <= 4:
            return 'weekdays'
        elif day == 5:
            return 'friday_holiday_evening'
        else:
            return 'saturday_holiday'

    def get_bio_month(self) -> str:
        """
        return a string representation to the bullet bio_month, example:
        'jan_feb', 'mar_apr', ...
        :return:
        """
        if self.date.month == 1 or self.date.month == 2:
            return 'jan_feb'
        if self.date.month == 3 or self.date.month == 4:
            return 'mar_apr'
        if self.date.month == 5 or self.date.month == 6:
            return 'may_jun'
        if self.date.month == 7 or self.date.month == 8:
            return 'jul_aug'
        if self.date.month == 9 or self.date.month == 10:
            return 'sep_oct'
        if self.date.month == 11 or self.date.month == 12:
            return 'nov_dec'

    def get_month(self) -> str:
        """
        return a string representation to the bullet month, example:
        'jan', 'feb', 'mar', 'apr', ...
        :return:
        """
        if self.date.month == 1:
            return 'jan'
        if self.date.month == 2:
            return 'feb'
        if self.date.month == 3:
            return 'mar'
        if self.date.month == 4:
            return 'apr'
        if self.date.month == 5:
            return 'may'
        if self.date.month == 6:
            return 'jun'
        if self.date.month == 7:
            return 'jul'
        if self.date.month == 8:
            return 'aug'
        if self.date.month == 9:
            return 'sep'
        if self.date.month == 10:
            return 'oct'
        if self.date.month == 11:
            return 'nov'
        if self.date.month == 12:
            return 'dev'

    def __radd__(self, other):
        production_amount = self.south_facility.production_amount + self.north_facility.production_amount
        return production_amount + other

    def __add__(self, other):
        production_amount = self.south_facility.production_amount + self.north_facility.production_amount
        return production_amount + other


class Taoz(Enum):
    SHEFEL = 0
    GEVA = 1
    PISGA = 2
