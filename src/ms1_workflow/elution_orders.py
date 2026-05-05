import itertools
from itertools import permutations

import pandas as pd


class ElutionOrderGenerator:
    """
    Generate possible elution orders from MS1 feature data.

    Works in two modes:
    1. Without standards:
       - Generates elution orders from the full dataset.

    2. With standards:
       - Splits metabolites into RT windows based on detected standards.
       - Generates elution orders separately for each RT window.
    """

    def __init__(self, rt_order_tolerance, elution_order_data, standards=None):
        self.rt_order_tolerance = rt_order_tolerance
        self.elution_order_data = (
            elution_order_data
            .drop_duplicates(subset=["Metabolite name"])
            .reset_index(drop=True)
        )
        self.standards = standards

    def generate_elution_orders(self):
        """
        Generate elution orders.

        Returns
        -------
        list or dict
            - list of elution orders if standards is None
            - dict of {window_index: elution_orders} if standards are provided
        """
        if self.standards is None:
            return self._generate_without_standards()

        if self.standards.empty:
            return self._generate_without_standards()

        return self._generate_with_standards()

    def _generate_without_standards(self):
        data = self.elution_order_data.sort_values(by="Reference RT").reset_index(drop=True)

        grouped_metabolites = self.group_metabolites(data)
        elution_orders = self.create_elution_permutations(grouped_metabolites)

        print(f"Generated {len(elution_orders)} possible elution orders.")
        return elution_orders

    def _generate_with_standards(self):
        rt_windows = self.assign_rt_windows()
        elution_orders = {}

        for window_idx, window_data in rt_windows.items():
            print(f"\nProcessing Window {window_idx} (Metabolites: {len(window_data)})")

            grouped_metabolites = self.group_metabolites(window_data)
            possible_orders = self.create_elution_permutations(grouped_metabolites)

            elution_orders[window_idx] = possible_orders

            print(f"Window {window_idx}: {len(possible_orders)} possible elution orders found.")
            for idx, order in enumerate(possible_orders[:3]):
                print(f"Example Order {idx + 1}: {order}")

        return elution_orders

    def assign_rt_windows(self):
        """
        Assign metabolites to RT windows using standard Reference RT values.

        In standards mode, RT windows are extended by rt_order_tolerance on both
        sides. This allows boundary metabolites to be included in adjacent windows
        when their Reference RT falls close to a standard-defined boundary.
        """
        standards_rt = sorted(self.standards["Reference RT"].tolist())
        rt_windows = {}

        for i in range(len(standards_rt) + 1):
            lower_bound = standards_rt[i - 1] if i > 0 else 0
            upper_bound = standards_rt[i] if i < len(standards_rt) else float("inf")

            extended_lower = max(0, lower_bound - self.rt_order_tolerance)
            extended_upper = upper_bound + self.rt_order_tolerance

            window_data = self.elution_order_data[
                (self.elution_order_data["Reference RT"] >= extended_lower)
                & (self.elution_order_data["Reference RT"] < extended_upper)
            ].copy()

            if not window_data.empty:
                window_data["RT Window"] = i
                window_data["RT Window Lower"] = lower_bound
                window_data["RT Window Upper"] = upper_bound
                window_data["Boundary Candidate"] = window_data["Reference RT"].apply(
                    lambda rt: (
                        "Yes"
                        if abs(rt - lower_bound) <= self.rt_order_tolerance
                        or abs(rt - upper_bound) <= self.rt_order_tolerance
                        else "No"
                    )
                )

                rt_windows[i] = window_data.reset_index(drop=True)

        return rt_windows

    def group_metabolites(self, data):
        """
        Group metabolites that can be swapped within the RT order tolerance.
        """
        data = data.sort_values(by="Reference RT").reset_index(drop=True)

        if data.empty:
            return []

        grouped_metabolites = []
        current_group = [data.iloc[0]["Metabolite name"]]

        for i in range(1, len(data)):
            prev_rt = data.iloc[i - 1]["Reference RT"]
            curr_rt = data.iloc[i]["Reference RT"]

            if abs(curr_rt - prev_rt) <= self.rt_order_tolerance:
                current_group.append(data.iloc[i]["Metabolite name"])
            else:
                grouped_metabolites.append(current_group)
                current_group = [data.iloc[i]["Metabolite name"]]

        grouped_metabolites.append(current_group)
        return grouped_metabolites

    def create_elution_permutations(self, grouped_metabolites):
        """
        Create all possible elution orders from grouped metabolites.
        """
        if not grouped_metabolites:
            return []

        all_permutations = [list(permutations(group)) for group in grouped_metabolites]
        all_orders = list(itertools.product(*all_permutations))

        return [list(sum(order_tuple, ())) for order_tuple in all_orders]

    def save_elution_orders(self, elution_orders, output_filename="outputs/Elution_Orders.xlsx"):
        """
        Save elution orders to Excel.

        Handles both:
        - list output from without-standards mode
        - dict output from with-standards mode
        """
        with pd.ExcelWriter(output_filename, engine="xlsxwriter") as writer:

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

        print(f"Elution orders saved to {output_filename}")