from enum import Enum
from datetime import date


class Facility:
    def __init__(self, production_amount=None, taoz_cost=None, secondary_taoz_cost=None, se_per_hour=None,
                 number_of_pumps=None, water_cubic_meter_price=None, kwh_energy_limit=None):
        self.production_amount: int = production_amount
        self.taoz_cost: float = taoz_cost
        self.secondary_taoz_cost: float = secondary_taoz_cost
        self.se_per_hour: float = se_per_hour
        self.number_of_pumps: int = number_of_pumps
        self.water_cubic_meter_price: float = water_cubic_meter_price
        self.kwh_energy_limit: int = kwh_energy_limit
        self.production_price: float = 0.0

    def calculate_price(self) -> None:
        """Calculates the production_price for the using facility."""
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
        day = self.date.day
        if day == 6 or 0 <= day <= 3:
            return 'weekdays'
        elif day == 4:
            return 'friday_holiday_evening'
        else:
            return 'saturday_holiday'


class Taoz(Enum):
    SHEFEL = 0
    GEVA = 1
    PISGA = 2
