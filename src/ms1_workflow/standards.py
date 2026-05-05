import pandas as pd


def standards_rt_filtering(
    mz_dial_data: pd.DataFrame,
    standards: pd.DataFrame,
    rt_alignment_tolerance: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Detect standards in mzDial data using RT alignment tolerance.

    Returns
    -------
    updated_mz_dial : pd.DataFrame
        mzDial data where detected standards are retained once.
    detected_standards : pd.DataFrame
        Standards detected within the RT tolerance window.
    """
    standards = standards.copy()

    standards["RT Lower"] = standards["Average Rt(min)"] - rt_alignment_tolerance
    standards["RT Upper"] = standards["Average Rt(min)"] + rt_alignment_tolerance

    detected_standards = mz_dial_data.merge(
        standards,
        on="Metabolite name",
        suffixes=("", "_standard"),
    ).query(
        "`Average Rt(min)` >= `RT Lower` and `Average Rt(min)` <= `RT Upper`"
    )

    detected_standards = detected_standards.drop_duplicates(
        subset=["Metabolite name"]
    )

    mz_dial_without_detected = mz_dial_data[
        ~mz_dial_data["Metabolite name"].isin(
            detected_standards["Metabolite name"]
        )
    ]

    updated_mz_dial = pd.concat(
        [mz_dial_without_detected, detected_standards],
        ignore_index=True,
    )

    updated_mz_dial = updated_mz_dial.sort_values(
        by="Reference RT"
    ).reset_index(drop=True)

    return updated_mz_dial, detected_standards


def determine_boundary_metabolites(
    data: pd.DataFrame,
    standards: pd.DataFrame,
    rt_order_tolerance: float,
) -> pd.DataFrame:
    """
    Mark metabolites close to standard Reference RT values.
    """
    data = data.copy()
    standards_rt = standards["Reference RT"].values

    data["Boundary Metabolite"] = data["Reference RT"].apply(
        lambda rt: "Yes"
        if any(abs(rt - standard_rt) <= rt_order_tolerance for standard_rt in standards_rt)
        else "No"
    )

    return data


def sort_filter_mzdial(
    mz_dial_data: pd.DataFrame,
    detected_standards: pd.DataFrame,
) -> pd.DataFrame:
    """
    Filter mzDial data using RT windows defined by detected standards.

    This preserves the previous standards-based workflow behavior.
    """
    if detected_standards.empty:
        return mz_dial_data.reset_index(drop=True)

    standards = detected_standards.sort_values(
        by="Reference RT"
    ).reset_index(drop=True)

    filtered_data = pd.DataFrame(columns=mz_dial_data.columns)

    lower_bound_av = 0
    lower_bound_ref = 0

    for i in range(len(standards) + 1):
        upper_bound_av = (
            standards.iloc[i]["Average Rt(min)"]
            if i < len(standards)
            else float("inf")
        )
        upper_bound_ref = (
            standards.iloc[i]["Reference RT"]
            if i < len(standards)
            else float("inf")
        )

        segment = mz_dial_data[
            (mz_dial_data["Reference RT"] >= lower_bound_ref)
            & (mz_dial_data["Reference RT"] < upper_bound_ref)
            & (mz_dial_data["Average Rt(min)"] >= lower_bound_av)
            & (mz_dial_data["Average Rt(min)"] < upper_bound_av)
        ]

        if not segment.empty:
            filtered_data = pd.concat(
                [filtered_data, segment],
                ignore_index=True,
            )

        lower_bound_av = upper_bound_av
        lower_bound_ref = upper_bound_ref

    return filtered_data.reset_index(drop=True)