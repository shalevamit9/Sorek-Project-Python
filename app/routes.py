from app import app, db
from flask import jsonify, request
from app.classes import MatrixBullet
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime

ROWS = 365
COLS = 24


def initialize_matrix(matrix: np.ndarray[MatrixBullet]) -> None:
    """
    initializing the matrix with dates and new empty MatrixBullet objects.
    receive an year property from the request body.
    """
    # get the year parameter from the request
    year = request.get_json()['year']
    iterating_date = date(year, 1, 1)
    delta = timedelta(days=1)

    rows = matrix.shape[0]
    cols = matrix.shape[1]

    for i in range(rows):
        for j in range(cols):
            matrix[i, j] = MatrixBullet()
            matrix[i, j].date = iterating_date
        iterating_date += delta


def parse_holidays():
    holidays = db.holidays.find_one({}, {'_id': 0})

    for holiday in holidays:
        holidays[holiday]['date'] = datetime.strptime(holidays[holiday]['date'], '%d/%m/%Y').date()

    return holidays


def parse_elections():
    elections = db.elections.find_one({}, {'_id': 0})

    for i in range(len(elections['dates'])):
        if elections['dates'][i] is not None:
            elections['dates'][i] = datetime.strptime(elections['dates'][i], '%d/%m/%Y').date()

    return elections


def get_holiday_day_representation(holidays, date_value) -> str:
    for holiday in holidays:
        if date_value == holidays[holiday]['date']:
            return holidays[holiday]['taoz']


def initialize_taoz(matrix: np.ndarray[MatrixBullet]) -> None:
    """
    Defining the taoz type as enum for each bullet in the matrix,
    holidays included.
    """
    taoz = db.taoz.find_one({}, {'_id': 0})

    holidays = parse_holidays()
    elections = parse_elections()

    rows = matrix.shape[0]
    cols = matrix.shape[1]

    for day in range(rows):
        current_date = matrix[day, 0].date
        is_holiday = True if current_date in holidays.values() else False
        is_election = True if current_date in elections['dates'] else False

        for hour in range(cols):
            cell = matrix[day, hour]

            day_representation = cell.get_day_representation()
            if is_holiday:
                day_representation = get_holiday_day_representation(holidays, current_date)
            elif is_election:
                day_representation = 'saturday_holiday'

            cell.define_taoz(taoz[cell.get_season()][day_representation][hour])


def initialize_starter_production_amount(matrix: np.ndarray[MatrixBullet]) -> None:
    """
    Initializing the starter production amount for each matrix bullet.
    It can be changed in the future.
    Initializing the max production amount for 2 pumps as start amount.
    """
    starter_production_amount_index = 1

    min_max_hp = db.min_max_hp.find_one({}, {'_id': 0})

    rows = matrix.shape[0]
    cols = matrix.shape[1]

    production_amount_sum = 0
    for i in range(rows):
        for j in range(cols):
            matrix[i, j].south_facility.production_amount = min_max_hp['south'][starter_production_amount_index]['max']
            matrix[i, j].north_facility.production_amount = min_max_hp['north'][starter_production_amount_index]['max']

            production_amount_sum += \
                matrix[i, j].south_facility.production_amount + matrix[i, j].north_facility.production_amount

            matrix[i, j].south_facility.number_of_pumps = \
                min_max_hp['south'][starter_production_amount_index]['hp_number']

            matrix[i, j].north_facility.number_of_pumps = \
                min_max_hp['north'][starter_production_amount_index]['hp_number']


def initialize_se(matrix: np.ndarray[MatrixBullet]) -> None:
    """
    Initialize the se (specific energy) for each cell in the matrix
    """
    se = db.specific_energy.find_one({}, {'_id': 0})

    rows = matrix.shape[0]
    cols = matrix.shape[1]

    for i in range(rows):
        for j in range(cols):
            # concat 'e_' to the number of pumps due to the key value in the object
            num_of_pumps = 'e_' + str(matrix[i, j].north_facility.number_of_pumps)
            month = matrix[i, j].date.month - 1

            matrix[i, j].north_facility.se_per_hour = se['north'][month][num_of_pumps]
            matrix[i, j].south_facility.se_per_hour = se['south'][month][num_of_pumps]


def initialize_kwh_price_and_limit(matrix: np.ndarray[MatrixBullet]) -> None:
    """
    Initialize the kwh price for each matrix bullet
    """

    rows = matrix.shape[0]
    cols = matrix.shape[1]

    taoz_cost_limit = db.taoz_cost_limit.find_one({}, {'_id': 0})
    for i in range(rows):
        for j in range(cols):
            month = matrix[i, j].date.month - 1
            taoz = matrix[i, j].taoz.name

            # initializing taoz_cost
            matrix[i, j].north_facility.taoz_cost = taoz_cost_limit['taoz_cost'][month][taoz]
            matrix[i, j].south_facility.taoz_cost = taoz_cost_limit['taoz_cost'][month][taoz]

            # initializing secondary_taoz_cost
            matrix[i, j].north_facility.secondary_taoz_cost = taoz_cost_limit['secondary_taoz_cost'][month][taoz]
            matrix[i, j].south_facility.secondary_taoz_cost = taoz_cost_limit['secondary_taoz_cost'][month][taoz]

            # initializing energy_limit
            matrix[i, j].north_facility.kwh_energy_limit = taoz_cost_limit['energy_limit'][month][taoz]
            matrix[i, j].south_facility.kwh_energy_limit = taoz_cost_limit['energy_limit'][month][taoz]


def initialize_production_price(matrix: np.ndarray[MatrixBullet]) -> None:
    """Initializing the production price for each matrix bullet"""

    rows = matrix.shape[0]
    cols = matrix.shape[1]

    for i in range(rows):
        for j in range(cols):
            matrix[i, j].north_facility.calculate_price()
            matrix[i, j].south_facility.calculate_price()


def initialize_price(matrix: np.ndarray[MatrixBullet]) -> None:
    """
    Initialize the price for each cell in the matrix
    """
    initialize_starter_production_amount(matrix)
    initialize_se(matrix)
    initialize_kwh_price_and_limit(matrix)
    initialize_production_price(matrix)


def fill_matrix(matrix: np.ndarray[MatrixBullet]) -> None:
    initialize_matrix(matrix)
    initialize_taoz(matrix)
    initialize_price(matrix)


# dfs = pd.read_excel('taoz.xls', sheet_name=None)
# df = pd.read_excel('taoz.xls')

@app.route('/start', methods=['POST'])
def start_algorithm():
    matrix = np.empty([ROWS, COLS], dtype=MatrixBullet)
    fill_matrix(matrix)
    return jsonify({'attr': 123})
