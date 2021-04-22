from enum import Enum


class Facility:
    def __init__(self, production_amount=None, taoz_cost=None, secondary_taoz_cost=None, se_per_hour=None,
                 number_of_pumps=None, water_cubic_meter_price=None, kwh_energy_limit=None):
        self.production_amount = production_amount
        self.taoz_cost = taoz_cost
        self.secondary_taoz_cost = secondary_taoz_cost
        self.se_per_hour = se_per_hour
        self.number_of_pumps = number_of_pumps
        self.water_cubic_meter_price = water_cubic_meter_price
        self.kwh_energy_limit = kwh_energy_limit
        self.production_price = None

    def calculate_price(self):
        self.production_price = self.se_per_hour * self.production_amount * self.taoz_cost


class MatrixBullet:
    def __init__(self, taoz=None, date=None):
        self.north_facility = Facility()
        self.south_facility = Facility()
        self.taoz = taoz
        self.date = date

    def define_taoz(self, taoz):
        taoz_to_assign = None
        if taoz == 'SHEFEL':
            taoz_to_assign = Taoz.SHEFEL
        elif taoz == 'GEVA':
            taoz_to_assign = Taoz.GEVA
        else:
            taoz_to_assign = Taoz.PISGA

        self.taoz = taoz_to_assign

    def get_week_day(self):
        return self.date.weekday()

    def get_season(self):
        month = self.date.month
        if month == 7 or month == 8:
            return 'summer'
        elif month == 1 or month == 2 or month == 12:
            return 'winter'
        else:
            return 'spring_autumn'

    def get_day_representation(self):
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
