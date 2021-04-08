from app import app
from flask import jsonify, request
from app.classes import MatrixBullet
import pandas as pd
import numpy as np
import json
from datetime import date, timedelta, datetime

ROWS = 365
COLS = 24
HOLIDAYS_FORMAT_FILE = 'holidays_format.json'
TAOZ_FORMAT_FILE = 'taoz_format.json'
ELECTIONS_FORMAT_FILE = 'elections_format.json'


def initialize_matrix(matrix):
    """
    initializing the matrix with dates and new empty MatrixBullet objects.
    :param matrix: matrix created with numpy, the initial matrix to fill
    """
    # get the year parameter from the request
    year = request.get_json()['year']
    iterating_date = date(year, 1, 1)
    delta = timedelta(days=1)

    for i in range(len(matrix)):
        for j in range(len(matrix[i])):
            matrix[i, j] = MatrixBullet()
            matrix[i, j].date = iterating_date
        iterating_date += delta


def parse_holidays():
    with open(HOLIDAYS_FORMAT_FILE, 'r') as f:
        holidays = json.load(f)
    for holiday in holidays:
        holidays[holiday]['date'] = datetime.strptime(holidays[holiday]['date'], '%d/%m/%Y').date()
    df = pd.DataFrame(holidays)
    return holidays


def parse_elections():
    with open(ELECTIONS_FORMAT_FILE, 'r') as f:
        elections = json.load(f)
    for i in range(len(elections['dates'])):
        if elections['dates'][i] is not None:
            elections['dates'][i] = datetime.strptime(elections['dates'][i], '%d/%m/%Y').date()

    return elections


def get_holiday_day_representation(holidays, date_value):
    for holiday in holidays:
        if date_value == holidays[holiday]['date']:
            return holidays[holiday]['taoz']


def initialize_taoz(matrix):
    with open(TAOZ_FORMAT_FILE, 'r') as f:
        taoz = json.load(f)

    holidays = parse_holidays()
    elections = parse_elections()

    for day in range(len(matrix)):
        current_date = matrix[day, 0].date
        is_holiday = True if current_date in holidays.values() else False
        is_election = True if current_date in elections['dates'] else False

        for hour in range(len(matrix[day])):
            cell = matrix[day, hour]

            day_representation = cell.get_day_representation()
            if is_holiday:
                day_representation = get_holiday_day_representation(holidays, current_date)
            elif is_election:
                day_representation = 'saturday_holiday'

            cell.define_taoz(taoz[cell.get_season()][day_representation][str(hour)])

    df = pd.DataFrame(matrix)
    return 'dummy return for breakpoint'


# def initialize_holidays(matrix):
#     with open('holidays_format', 'r') as f:
#         taoz = json.load(f)


def fill_matrix(matrix):
    initialize_matrix(matrix)
    initialize_taoz(matrix)
    # initialize_holidays(matrix)


# dfs = pd.read_excel('taoz.xls', sheet_name=None)
# df = pd.read_excel('taoz.xls')

@app.route('/start', methods=['POST'])
def start_algorithm():
    matrix = np.empty([ROWS, COLS], dtype=MatrixBullet)
    fill_matrix(matrix)
    return jsonify({'attr': 123})
