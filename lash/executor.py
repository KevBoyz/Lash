# This file is here only to return the path of this directory to
# functions that access intern files of the package
import os


def abs_path_data():
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')
