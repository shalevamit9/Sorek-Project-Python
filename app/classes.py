from enum import Enum


class MatrixBullet:
    def __init__(
            self, production_amount=None, taoz=None, number_of_pumps=None, se_per_hour=None, kwh_per_hour=None,
            facility=None, water_cubic_meters=None, date=None):
        self.water_cubic_meters = water_cubic_meters
        self.facility = facility
        self.kwh_per_hour = kwh_per_hour
        self.se_per_hour = se_per_hour
        self.number_of_pumps = number_of_pumps
        self.production_amount = production_amount
        self.taoz = taoz
        self.date = date
        # self.price = self.se_per_hour * self.production_amount * self.kwh_per_hour

    def define_taoz(self, taoz):
        taoz_to_assign = None
        if taoz == 'SHEFEL':
            taoz_to_assign = Taoz.SHEFEL
        elif taoz == 'GEVA':
            taoz_to_assign = Taoz.GEVA
        else:
            taoz_to_assign = Taoz.PISGA

        self.taoz = taoz_to_assign

    def get_price(self):
        return self.se_per_hour * self.production_amount * self.kwh_per_hour

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
