from enum import Enum


class Facility:
    def __init__(self, production_amount, kwh_per_hour_price, se_per_hour, number_of_pumps,
                 water_cubic_meter_price):
        self.production_amount = production_amount
        self.kwh_per_hour_price = kwh_per_hour_price
        self.se_per_hour = se_per_hour
        self.number_of_pumps = number_of_pumps
        self.water_cubic_meter_price = water_cubic_meter_price
        self.production_price = None

    def calculate_price(self):
        self.production_price = self.se_per_hour * self.production_amount * self.kwh_per_hour_price


class NorthFacility(Facility):
    def __init__(self, production_amount=None, se_per_hour=None, number_of_pumps=None,
                 water_cubic_meter_price=None, kwh_per_hour_price=None):
        super().__init__(production_amount, kwh_per_hour_price, se_per_hour, number_of_pumps, water_cubic_meter_price)


class SouthFacility(Facility):
    def __init__(self, production_amount=None, se_per_hour=None, number_of_pumps=None, water_cubic_meter_price=None,
                 kwh_per_hour_price=None):
        super().__init__(production_amount, kwh_per_hour_price, se_per_hour, number_of_pumps, water_cubic_meter_price)


class MatrixBullet:
    def __init__(
            self, south_production_amount=None, north_production_amount=None, taoz=None, number_of_pumps=None,
            se_per_hour=None, kwh_per_hour=None, water_cubic_meters=None, date=None):
        self.north_facility = NorthFacility()
        self.south_facility = SouthFacility()
        self.taoz = taoz
        self.date = date
        # self.price = self.se_per_hour * self.production_amount * self.kwh_per_hour
        # self.north_price = self.se_per_hour * self.north_production_amount * self.kwh_per_hour
        # self.south_price = self.se_per_hour * self.south_production_amount * self.kwh_per_hour
        # self.north_price = None
        # self.south_price = None

    # def calculate_price(self):
    #     self.north_price = self.se_per_hour * self.north_production_amount * self.kwh_per_hour
    #     self.south_price = self.se_per_hour * self.south_production_amount * self.kwh_per_hour

    def define_taoz(self, taoz):
        taoz_to_assign = None
        if taoz == 'SHEFEL':
            taoz_to_assign = Taoz.SHEFEL
        elif taoz == 'GEVA':
            taoz_to_assign = Taoz.GEVA
        else:
            taoz_to_assign = Taoz.PISGA

        self.taoz = taoz_to_assign

    # def get_price(self):
    #     return self.se_per_hour * self.production_amount * self.kwh_per_hour

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
