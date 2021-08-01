from datetime import date, timedelta, datetime
from typing import Tuple

import numpy as np
from nptyping import NDArray
from flask import jsonify, request

from app import app, db
from app.classes import Facility, MatrixBullet

from lib.xl_writer_reader import write_plan_to_xl

ROWS = 365
COLS = 24

min_max_hp = db.min_max_hp.find_one({}, {'_id': 0})
se = db.specific_energy.find_one({}, {'_id': 0})

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
            cell: MatrixBullet = matrix[day, hour]

            day_representation = cell.get_day_representation()
            if is_holiday:
                day_representation = get_holiday_day_representation(holidays, current_date)
            elif is_election:
                day_representation = 'saturday_holiday'

            cell.define_taoz(taoz[cell.get_season()][day_representation][hour])


def initialize_shutdown_dates(matrix: NDArray[MatrixBullet]) -> None:
    """Initializing the shutdown dates with specified hours in the same date"""
    shutdown_dates = db.shutdown_dates.find_one({}, {'_id': 0})

    for shutdown_day in shutdown_dates['days']:
        day_index = datetime.strptime(shutdown_day['date'], '%d/%m/%Y').date().timetuple().tm_yday - 1
        for hour in range(shutdown_day['from_hour'], shutdown_day['to_hour']):
            matrix[day_index, hour].north_facility.shutdown = not shutdown_day['is_south_facility']
            matrix[day_index, hour].south_facility.shutdown = shutdown_day['is_south_facility']


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
            current_bullet: MatrixBullet = matrix[i, j]

            if current_bullet.north_facility.shutdown is False:
                current_bullet.north_facility.production_amount = \
                    min_max_hp['north'][starter_production_amount_index]['max']
                current_bullet.north_facility.number_of_pumps = \
                    min_max_hp['north'][starter_production_amount_index]['hp_number']
                production_amount_sum += current_bullet.north_facility.production_amount

            if current_bullet.south_facility.shutdown is False:
                current_bullet.south_facility.production_amount = \
                    min_max_hp['south'][starter_production_amount_index]['max']
                current_bullet.south_facility.number_of_pumps = \
                    min_max_hp['south'][starter_production_amount_index]['hp_number']
                production_amount_sum += current_bullet.south_facility.production_amount


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
            bullet: MatrixBullet = matrix[i, j]
            north_num_of_pumps = 'e_' + str(bullet.north_facility.number_of_pumps)
            south_num_of_pumps = 'e_' + str(bullet.south_facility.number_of_pumps)
            month = bullet.date.month - 1

            if bullet.north_facility.shutdown is False:
                bullet.north_facility.se_per_hour = se['north'][month][north_num_of_pumps]
            if bullet.south_facility.shutdown is False:
                bullet.south_facility.se_per_hour = se['south'][month][south_num_of_pumps]


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
    """Initialize the price for each cell in the matrix"""
    initialize_starter_production_amount(matrix)
    initialize_se(matrix)
    initialize_kwh_price_and_limit(matrix)
    initialize_production_price(matrix)


def fill_matrix(matrix: NDArray[MatrixBullet]) -> None:
    initialize_matrix(matrix)
    initialize_taoz(matrix)
    # initialize_shutdown_dates(matrix)
    initialize_price(matrix)


def update_hour(hour: MatrixBullet, is_north: bool, hourly_limit: int) -> None:
    """
    updates a specific hour number of pumps, se, production amount
    """
    global min_max_hp
    global se

    month = hour.date.month - 1

    is_north_updateable = is_north and hour.north_facility.number_of_pumps < 5
    if is_north_updateable:
        facility: Facility = hour.north_facility
        facility.number_of_pumps += 1
        facility.se_per_hour = se['north'][month]['e_' + str(facility.number_of_pumps)]
        if min_max_hp['north'][facility.number_of_pumps - 1]['max'] <= hourly_limit:
            facility.production_amount = min_max_hp['north'][facility.number_of_pumps - 1]['max']
        else:
            facility.production_amount = hourly_limit
    elif not is_north and hour.south_facility.number_of_pumps < 5:
        facility: Facility = hour.south_facility
        facility.number_of_pumps += 1
        facility.se_per_hour = se['north'][month]['e_' + str(facility.number_of_pumps)]
        if min_max_hp['south'][facility.number_of_pumps - 1]['max'] <= hourly_limit:
            facility.production_amount = min_max_hp['south'][facility.number_of_pumps - 1]['max']
        else:
            facility.production_amount = hourly_limit

    hour.calculate_price()


def get_cheapest_hour_of_day(day: NDArray[MatrixBullet], hourly_limit: int) -> Tuple[MatrixBullet, bool]:
    """
    finds the MIN hour of a specific day and return it with a flag
    that checks if the north or south facility is in the limit
    """
    cheapest_hour: MatrixBullet = day[0]
    is_north = False

    for hour in day:
        # for intellisense
        hour: MatrixBullet = hour

        is_cheaper_hour = hour.price < cheapest_hour.price

        is_in_north_limit = hour.north_facility.production_amount < hourly_limit
        is_in_south_limit = hour.south_facility.production_amount < hourly_limit
        if is_cheaper_hour \
            and is_in_north_limit \
            and not hour.north_facility.shutdown \
            and hour.south_facility.number_of_pumps > hour.north_facility.number_of_pumps:
            cheapest_hour = hour
            is_north = True
        elif is_cheaper_hour and is_in_south_limit and not hour.south_facility.shutdown:
            cheapest_hour = hour
            is_north = False

    return cheapest_hour, is_north


def update_daily_production(matrix: NDArray[MatrixBullet], production_limits) -> None:
    rows = matrix.shape[0]
    cols = matrix.shape[1]

    for i in range(rows):
        for j in range(cols):
            bullet: MatrixBullet = matrix[i, j]
            bio_month = bullet.get_bio_month()
            limits = production_limits[bio_month]

            hourly_production_amount = bullet.north_facility.production_amount + bullet.south_facility.production_amount
            if hourly_production_amount > limits['hourly']['max']:
                break

            daily_production_amount = sum(matrix[i])
            while daily_production_amount < limits['daily']['min'] \
                and not bullet.north_facility.shutdown \
                    and not bullet.south_facility.shutdown:
                # go to the cheapest hour of the day, increase the production amount as much as possible
                cheapest_hour, is_north = get_cheapest_hour_of_day(matrix[i], limits['hourly']['max'])
                update_hour(cheapest_hour, is_north, limits['hourly']['max'])
                daily_production_amount = sum(matrix[i])


def get_bio_month_production_amount(matrix: NDArray[MatrixBullet], start: int, end: int) -> int:
    months_sum = 0
    for i in range(start, end + 1):
        months_sum += sum(matrix[i])

    return months_sum


def get_month_day_indices(matrix: NDArray[MatrixBullet], months: list[int]):
    """
    return a tuple of two integers that symbolize range to iterate in the main matrix
    """
    rows = matrix.shape[0]

    if months[1] == 12:
        return rows - 61, rows - 1

    start = -1
    for i in range(rows):
        bullet: MatrixBullet = matrix[i, 0]
        
        if bullet.date.month == months[0] and start == -1:
            start = i
        elif bullet.date.month > months[1]:
            end = i - 1

            return start, end


def get_cheapest_hour_of_bio_month(matrix: NDArray, start: int, end: int, production_limits):
    cheapest_hour: MatrixBullet = matrix[start, 0]
    is_north = False

    cols = matrix.shape[1]

    for i in range(start, end + 1):
        for j in range(cols):
            # for intellisense
            hour: MatrixBullet = matrix[i, j]

            is_cheaper_hour = hour.price < cheapest_hour.price
            
            hourly_limit = production_limits[hour.get_bio_month()]['hourly']['max']

            is_in_north_hourly_limit = hour.north_facility.production_amount < hourly_limit
            is_in_south_hourly_limit = hour.south_facility.production_amount < hourly_limit
            if is_cheaper_hour \
                and is_in_north_hourly_limit \
                and not hour.north_facility.shutdown \
                and hour.south_facility.number_of_pumps > hour.north_facility.number_of_pumps:
                cheapest_hour = hour
                is_north = True
            elif is_cheaper_hour and is_in_south_hourly_limit and not hour.south_facility.shutdown:
                cheapest_hour = hour
                is_north = False

    return cheapest_hour, is_north
 

def update_bio_month_production(matrix: NDArray[MatrixBullet], production_limits) -> None:
    jan_feb_start_day, jan_feb_end_day = get_month_day_indices(matrix, [1, 2])
    jan_feb_prod_amount = get_bio_month_production_amount(matrix, jan_feb_start_day, jan_feb_end_day)
    while jan_feb_prod_amount < production_limits['jan_feb']['biomonthly']['min']:
        cheapest_hour, is_north = get_cheapest_hour_of_bio_month(matrix, jan_feb_start_day, jan_feb_end_day, production_limits)
        update_hour(cheapest_hour, is_north, production_limits['jan_feb']['hourly']['max'])
        jan_feb_prod_amount = get_bio_month_production_amount(matrix, jan_feb_start_day, jan_feb_end_day)
    
    mar_apr_start_day, mar_apr_end_day = get_month_day_indices(matrix, [3, 4])
    mar_apr_prod_amount = get_bio_month_production_amount(matrix, mar_apr_start_day, mar_apr_end_day)
    while mar_apr_prod_amount < production_limits['mar_apr']['biomonthly']['min']:
        cheapest_hour, is_north = get_cheapest_hour_of_bio_month(matrix, mar_apr_start_day, mar_apr_end_day, production_limits)
        update_hour(cheapest_hour, is_north, production_limits['mar_apr']['hourly']['max'])
        mar_apr_prod_amount = get_bio_month_production_amount(matrix, mar_apr_start_day, mar_apr_end_day)

    may_jun_start_day, may_jun_end_day = get_month_day_indices(matrix, [5, 6])
    may_jun_prod_amount = get_bio_month_production_amount(matrix, may_jun_start_day, may_jun_end_day)
    while may_jun_prod_amount < production_limits['may_jun']['biomonthly']['min']:
        cheapest_hour, is_north = get_cheapest_hour_of_bio_month(matrix, may_jun_start_day, may_jun_end_day, production_limits)
        update_hour(cheapest_hour, is_north, production_limits['may_jun']['hourly']['max'])
        may_jun_prod_amount = get_bio_month_production_amount(matrix, may_jun_start_day, may_jun_end_day)

    jul_aug_start_day, jul_aug_end_day = get_month_day_indices(matrix, [7, 8])
    jul_aug_prod_amount = get_bio_month_production_amount(matrix, jul_aug_start_day, jul_aug_end_day)
    while jul_aug_prod_amount < production_limits['jul_aug']['biomonthly']['min']:
        cheapest_hour, is_north = get_cheapest_hour_of_bio_month(matrix, jul_aug_start_day, jul_aug_end_day, production_limits)
        update_hour(cheapest_hour, is_north, production_limits['jul_aug']['hourly']['max'])
        jul_aug_prod_amount = get_bio_month_production_amount(matrix, jul_aug_start_day, jul_aug_end_day)

    sep_oct_start_day, sep_oct_end_day = get_month_day_indices(matrix, [9, 10])
    sep_oct_prod_amount = get_bio_month_production_amount(matrix, sep_oct_start_day, sep_oct_end_day)
    while sep_oct_prod_amount < production_limits['sep_oct']['biomonthly']['min']:
        cheapest_hour, is_north = get_cheapest_hour_of_bio_month(matrix, sep_oct_start_day, sep_oct_end_day, production_limits)
        update_hour(cheapest_hour, is_north, production_limits['sep_oct']['hourly']['max'])
        sep_oct_prod_amount = get_bio_month_production_amount(matrix, sep_oct_start_day, sep_oct_end_day)

    nov_dec_start_day, nov_dec_end_day = get_month_day_indices(matrix, [11, 12])
    nov_dec_prod_amount = get_bio_month_production_amount(matrix, nov_dec_start_day, nov_dec_end_day)
    while nov_dec_prod_amount < production_limits['nov_dec']['biomonthly']['min']:
        cheapest_hour, is_north = get_cheapest_hour_of_bio_month(matrix, nov_dec_start_day, nov_dec_end_day, production_limits)
        update_hour(cheapest_hour, is_north, production_limits['nov_dec']['hourly']['max'])
        nov_dec_prod_amount = get_bio_month_production_amount(matrix, nov_dec_start_day, nov_dec_end_day)


def get_cheapest_hour(matrix: NDArray[MatrixBullet]) -> MatrixBullet:
    rows = matrix.shape[0]
    cols = matrix.shape[1]

    cheapest_hour: MatrixBullet = matrix[0, 0]

    for i in range(rows):
        for j in range(cols):
            bullet: MatrixBullet = matrix[i, j]

            if bullet.price < cheapest_hour.price:
                cheapest_hour = bullet
    
    return cheapest_hour


def calculate_production_amount_to_add(bullet: MatrixBullet) -> int:
    """return the production amount for an hour, return -1 if cannot add production to the hour"""
    if not bullet.north_facility.shutdown and bullet.north_facility.number_of_pumps < 5:
        return min_max_hp['north'][bullet.north_facility.number_of_pumps]['max'] - bullet.north_facility.production_amount
    if not bullet.south_facility.shutdown and bullet.south_facility.number_of_pumps < 5:
        return min_max_hp['south'][bullet.south_facility.number_of_pumps]['max'] - bullet.south_facility.production_amount

    return -1


def update_cheapest_hours(matrix: NDArray[MatrixBullet], production_limits) -> None:
    target_amount = request.get_json()['target']
    current_production_amount = sum(sum(matrix))

    while current_production_amount < target_amount:
        bullet = get_cheapest_hour(matrix)

        production_amount_to_add = calculate_production_amount_to_add(bullet)
        is_over_target = current_production_amount + calculate_production_amount_to_add(bullet) > target_amount
        if is_over_target:
            production_amount_to_add = target_amount - current_production_amount

            if not bullet.north_facility.shutdown and bullet.north_facility.number_of_pumps < 5:
                bullet.north_facility.production_amount += production_amount_to_add
            elif not bullet.south_facility.shutdown and bullet.south_facility.number_of_pumps < 5:
                bullet.south_facility.production_amount += production_amount_to_add
        else:
            if not bullet.north_facility.shutdown and bullet.north_facility.number_of_pumps < 5:
                update_hour(bullet, True, production_limits[bullet.get_bio_month()]['hourly']['max'])
            elif not bullet.south_facility.shutdown and bullet.south_facility.number_of_pumps < 5:
                update_hour(bullet, False, production_limits[bullet.get_bio_month()]['hourly']['max'])

        current_production_amount += production_amount_to_add


def update_expensive_hours(matrix: NDArray[MatrixBullet], production_limits) -> None:
    target_amount = request.get_json()['target']
    current_production_amount = sum(sum(matrix))

    rows = matrix.shape[0]
    cols = matrix.shape[1]

    for i in range(rows):
        for j in range(cols):
            bullet: MatrixBullet = matrix[i, j]


def update_yearly_production(matrix: NDArray[MatrixBullet], production_limits) -> None:
    target_amount = request.get_json()['target']
    current_production_amount = sum(sum(matrix))

    # produce more in cheap hours
    if target_amount > current_production_amount:
        update_cheapest_hours(matrix, production_limits)
    else: # produce less in expensive hours
        update_expensive_hours(matrix, production_limits)


def update_production_price_till_target(matrix: NDArray[MatrixBullet]) -> None:
    """
    Update the matrix with new amount and price consistently
    until the target price is reached, the price will be received
    from the request body with the name 'target'
    """
    production_limits = db.production_limits.find_one({}, {'_id': 0})

    # matrix, production_limits
    update_daily_production(matrix, production_limits)
    update_bio_month_production(matrix, production_limits)
    update_yearly_production(matrix, production_limits)


@app.route('/start', methods=['POST'])
def start_algorithm():
    matrix = np.empty([ROWS, COLS], dtype=MatrixBullet)
    fill_matrix(matrix)
    update_production_price_till_target(matrix)
    write_plan_to_xl(matrix)
    return jsonify({'status': 'success'})
