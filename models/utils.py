# ./models/utils.py

from functools import wraps
from flask import session, redirect, url_for
from bson import ObjectId
import datetime

def validate_object_id(id_str):
    try:
        return ObjectId(id_str)
    except:
        return None

def is_valid_object_id(id_str):
    return validate_object_id(id_str) is not None

class DatabaseError(Exception):
    pass