
from backend.big_five_service import (
    TRAITS,
    prepare_profile_data as backend_prepare_profile_data,
    analyze_big_five as backend_analyze_big_five,
)


def prepare_profile_data(data):
    return backend_prepare_profile_data(data)


def analyze_big_five(data):
    return backend_analyze_big_five(data)
