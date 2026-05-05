from pathlib import Path

import pandas as pd


def load_file(path: str | Path) -> pd.DataFrame:
    """
    Load CSV or Excel data from disk.
    """
    path = Path(path)

    if path.suffix.lower() == ".xlsx":
        return pd.read_excel(path)

    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)

    raise ValueError("Unsupported file format. Please use .csv or .xlsx")


def save_without_standards_data(
    original_data: pd.DataFrame,
    mass_filtered_data: pd.DataFrame,
    output_dir: str | Path = "outputs/without_standards",
) -> None:
    """
    Save original and mass-filtered data for the workflow without standards.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "Original_and_Filtered_Data.xlsx"

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        original_data.to_excel(writer, sheet_name="Original_Data", index=False)
        mass_filtered_data.to_excel(writer, sheet_name="Mass_Filtered_Data", index=False)

    print(f"Saved data to {output_path}")


def save_with_standards_data(
    original_data: pd.DataFrame,
    standards_filtered: pd.DataFrame,
    mass_filtered: pd.DataFrame,
    elution_order_data: pd.DataFrame,
    output_dir: str | Path = "outputs/with_standards",
) -> None:
    """
    Save intermediate data for the standards-based workflow.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "Filtered_Data.xlsx"

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        original_data.to_excel(writer, sheet_name="Original Data", index=False)
        standards_filtered.to_excel(writer, sheet_name="Standards Filtered Data", index=False)
        mass_filtered.to_excel(writer, sheet_name="Mass Filtered Data", index=False)
        elution_order_data.to_excel(writer, sheet_name="Data to Elution Orders", index=False)

    print(f"Saved data to {output_path}")


def save_elution_orders(
    elution_orders,
    output_path: str | Path,
) -> None:
    """
    Save elution orders to Excel.

    Supports:
    - list of orders
    - dict of window_index -> orders
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        if isinstance(elution_orders, dict):
            for window_idx, orders in elution_orders.items():
                df = pd.DataFrame({
                    "Elution Order": [", ".join(order) for order in orders]
                })
                df.to_excel(writer, sheet_name=f"Window {window_idx}", index=False)
        else:
            df = pd.DataFrame({
                "Elution Order": [", ".join(order) for order in elution_orders]
            })
            df.to_excel(writer, sheet_name="Elution Orders", index=False)

    print(f"Saved elution orders to {output_path}")