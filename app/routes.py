from app import app
from flask import jsonify, request
from app.classes import MatrixBullet
import pandas as pd
import numpy as np
import json
from datetime import date, timedelta

ROWS = 365
COLS = 24


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


def initialize_taoz(matrix):
    with open('taoz_format.json', 'r') as f:
        taoz = json.load(f)
    with open('holidays_format.json', 'r') as f:
        holidays = json.load(f)
    for day in range(len(matrix)):
        # is_holiday =
        for hour in range(len(matrix[day])):
            cell = matrix[day, hour]

            cell.define_taoz(taoz[cell.get_season()][cell.get_day_representation()][str(hour)])

    # print(taoz['summer']['weekdays']['0'])
    return taoz


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
