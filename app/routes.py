from datetime import date, timedelta, datetime

import numpy as np
from nptyping import NDArray
from flask import jsonify, request

from app import app, db
from app.classes import MatrixBullet

ROWS = 365
COLS = 24

total_sum_production_amount = 0


def initialize_matrix(matrix: NDArray[MatrixBullet]) -> None:
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


def initialize_taoz(matrix: NDArray[MatrixBullet]) -> None:
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


def initialize_starter_production_amount(matrix: NDArray[MatrixBullet]) -> None:
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

    global total_sum_production_amount
    total_sum_production_amount = production_amount_sum


def initialize_se(matrix: NDArray[MatrixBullet]) -> None:
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


def initialize_kwh_price_and_limit(matrix: NDArray[MatrixBullet]) -> None:
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


def initialize_production_price(matrix: NDArray[MatrixBullet]) -> None:
    """Initializing the production price for each matrix bullet"""

    rows = matrix.shape[0]
    cols = matrix.shape[1]

    for i in range(rows):
        for j in range(cols):
            matrix[i, j].calculate_price()


def initialize_price(matrix: NDArray[MatrixBullet]) -> None:
    """
    Initialize the price for each cell in the matrix
    """
    initialize_starter_production_amount(matrix)
    initialize_se(matrix)
    initialize_kwh_price_and_limit(matrix)
    initialize_production_price(matrix)


def fill_matrix(matrix: NDArray[MatrixBullet]) -> None:
    initialize_matrix(matrix)
    initialize_taoz(matrix)
    initialize_price(matrix)


def update_bullet_pumps_num(bullet: MatrixBullet, min_max_hp) -> None:
    """add one pump usage to the facility at the a specific hour"""
    bullet.south_facility.number_of_pumps += 1
    bullet.north_facility.number_of_pumps += 1


def update_bullet_production_amount(bullet: MatrixBullet, min_max_hp) -> None:
    """update the production amount for a specific hour based on the amount of pumps to use"""
    global total_sum_production_amount
    total_sum_production_amount -= \
        bullet.north_facility.production_amount + bullet.south_facility.production_amount

    num_of_pumps = bullet.north_facility.number_of_pumps - 1
    bullet.north_facility.production_amount = min_max_hp['north'][num_of_pumps]['max']
    bullet.south_facility.production_amount = min_max_hp['south'][num_of_pumps]['max']

    total_sum_production_amount += \
        bullet.north_facility.production_amount + bullet.south_facility.production_amount


def update_bullet(bullet: MatrixBullet, min_max_hp):
    """
    update bullet num of pumps to use,
    production amount
    and calculates the new price for a specific hour
    """
    update_bullet_pumps_num(bullet, min_max_hp)
    update_bullet_production_amount(bullet, min_max_hp)
    bullet.calculate_price()


def find_min_production_amount_bullet(matrix: NDArray[MatrixBullet]) -> MatrixBullet:
    """Find and return the MatrixBullet in the matrix with the minimal price"""
    tmp_min_price = matrix[0, 0].price
    tmp_min_bullet = matrix[0, 0]
    rows = matrix.shape[0]
    cols = matrix.shape[1]

    for i in range(rows):
        for j in range(cols):
            if tmp_min_price > matrix[i, j].price:
                tmp_min_price = matrix[i, j].price
                tmp_min_bullet = matrix[i, j]

    return tmp_min_bullet


def update_production_price_till_target(matrix: NDArray[MatrixBullet]) -> None:
    """
    Update the matrix with new amount and price consistently
    until the target price is reached, the price will be received
    from the request body with the name 'target'
    """
    global total_sum_production_amount
    target_amount = request.get_json()['target']

    min_max_hp = db.min_max_hp.find_one({}, {'_id': 0})

    while total_sum_production_amount <= target_amount:
        min_price_bullet = find_min_production_amount_bullet(matrix)
        update_bullet(min_price_bullet, min_max_hp)

    while total_sum_production_amount > target_amount:
        max_price_bullet = find_max_production_amount_bullet(matrix)


def decrease_until_limit(bullet: MatrixBullet, min_max_hp):
    min_prod_amount_north = min_max_hp['north'][bullet.north_facility.number_of_pumps]['min']
    min_prod_amount_south = min_max_hp['south'][bullet.south_facility.number_of_pumps]['min']
    target_amount = request.get_json()['target']
    global total_sum_production_amount

    pumps_min_production = \
        total_sum_production_amount - bullet.north_facility.production_amount + min_prod_amount_north
    if pumps_min_production >= target_amount:
        if bullet.north_facility.number_of_pumps >= 2:
            bullet.north_facility.number_of_pumps -= 1
            bullet.north_facility.production_amount =\
                min_max_hp['north'][bullet.north_facility.number_of_pumps]['max']
        else:
            bullet.north_facility.production_amount =\
                min_max_hp['north'][bullet.north_facility.number_of_pumps]['min']

        bullet.calculate_price()


def find_max_production_amount_bullet(matrix: NDArray[MatrixBullet]) -> MatrixBullet:
    """Find and return the MatrixBullet in the matrix with the minimal price"""
    tmp_max_price = matrix[0, 0].price
    tmp_max_bullet = matrix[0, 0]
    rows = matrix.shape[0]
    cols = matrix.shape[1]

    for i in range(rows):
        for j in range(cols):
            if tmp_max_price < matrix[i, j].price:
                tmp_max_price = matrix[i, j].price
                tmp_max_bullet = matrix[i, j]

    return tmp_max_bullet


# dfs = pd.read_excel('taoz.xls', sheet_name=None)
# df = pd.read_excel('taoz.xls')

@app.route('/start', methods=['POST'])
def start_algorithm():
    matrix = np.empty([ROWS, COLS], dtype=MatrixBullet)
    fill_matrix(matrix)
    update_production_price_till_target(matrix)
    return jsonify({'attr': 123})
