import pandas as pd


def mass_filtering(data: pd.DataFrame, ppm_threshold: float) -> pd.DataFrame:
    """
    Filter mzDial features based on ppm tolerance.

    A feature is retained if the absolute difference between Average Mz
    and Reference m/z is within the ppm-based tolerance.
    """
    data = data.copy()

    ppm_tolerance = data["Reference m/z"] * (ppm_threshold / 1e6)

    filtered_data = data[
        (data["Average Mz"] - data["Reference m/z"]).abs() <= ppm_tolerance
    ]

    return filtered_data.reset_index(drop=True)