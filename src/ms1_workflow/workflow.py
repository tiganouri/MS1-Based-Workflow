from pathlib import Path

import pandas as pd

from .filtering import mass_filtering
from .standards import (
    determine_boundary_metabolites,
    sort_filter_mzdial,
    standards_rt_filtering,
)
from .elution_orders import ElutionOrderGenerator
from .combinations import ElutionCombinationProcessor
from .io import (
    save_elution_orders,
    save_with_standards_data,
    save_without_standards_data,
)


class MS1Workflow:
    """
    Main MS1 workflow.

    This class supports two modes:

    1. Without standards:
       - mass filtering
       - elution order generation
       - valid combination generation

    2. With standards:
       - mass filtering
       - standard detection by RT alignment
       - RT-window filtering
       - elution order generation per RT window
       - valid combination generation per RT window
    """

    def __init__(
        self,
        ppm_threshold: float = 10,
        rt_order_tolerance: float = 0.01,
        rt_alignment_tolerance: float = 0.01,
        output_dir: str | Path = "outputs",
    ):
        self.ppm_threshold = ppm_threshold
        self.rt_order_tolerance = rt_order_tolerance
        self.rt_alignment_tolerance = rt_alignment_tolerance
        self.output_dir = Path(output_dir)

    def run_without_standards(self, mz_dial_data: pd.DataFrame):
        """
        Run the MS1 workflow without internal standards.
        """
        output_dir = self.output_dir / "without_standards"
        output_dir.mkdir(parents=True, exist_ok=True)

        print("Step 1: Mass filtering")
        original_data = mz_dial_data.copy()
        mass_filtered_data = mass_filtering(
            mz_dial_data,
            ppm_threshold=self.ppm_threshold,
        )

        save_without_standards_data(
            original_data=original_data,
            mass_filtered_data=mass_filtered_data,
            output_dir=output_dir,
        )

        print("Step 2: Generating elution orders")
        generator = ElutionOrderGenerator(
            rt_order_tolerance=self.rt_order_tolerance,
            elution_order_data=mass_filtered_data,
            standards=None,
        )

        elution_orders = generator.generate_elution_orders()

        save_elution_orders(
            elution_orders,
            output_path=output_dir / "Possible_Elution_Orders.xlsx",
        )

        print("Step 3: Generating valid combinations")
        processor = ElutionCombinationProcessor(
            elution_orders=elution_orders,
            elution_order_data=mass_filtered_data,
            standards=None,
            output_dir=output_dir / "Elution_Results",
        )
        processor.run()

        print("Workflow without standards complete.")

        return {
            "original_data": original_data,
            "mass_filtered_data": mass_filtered_data,
            "elution_orders": elution_orders,
        }

    def run_with_standards(
        self,
        mz_dial_data: pd.DataFrame,
        standards: pd.DataFrame,
    ):
        """
        Run the MS1 workflow using internal standards.
        """
        output_dir = self.output_dir / "with_standards"
        output_dir.mkdir(parents=True, exist_ok=True)

        print("Step 1: Mass filtering")
        original_data = mz_dial_data.copy()
        mass_filtered_data = mass_filtering(
            mz_dial_data,
            ppm_threshold=self.ppm_threshold,
        )

        print("Step 2: Detecting standards")
        updated_mz_dial, detected_standards = standards_rt_filtering(
            mz_dial_data=mass_filtered_data,
            standards=standards,
            rt_alignment_tolerance=self.rt_alignment_tolerance,
        )

        if detected_standards.empty:
            print("Warning: no standards detected using the selected RT tolerance.")

        print("Step 3: Preparing data for elution orders")
        mass_filtered_with_boundary = determine_boundary_metabolites(
            data=mass_filtered_data,
            standards=standards,
            rt_order_tolerance=self.rt_order_tolerance,
        )

        elution_order_data = sort_filter_mzdial(
            mz_dial_data=updated_mz_dial,
            detected_standards=detected_standards,
        )

        save_with_standards_data(
            original_data=original_data,
            standards_filtered=detected_standards,
            mass_filtered=mass_filtered_with_boundary,
            elution_order_data=elution_order_data,
            output_dir=output_dir,
        )

        print("Step 4: Generating elution orders")
        generator = ElutionOrderGenerator(
            rt_order_tolerance=self.rt_order_tolerance,
            elution_order_data=elution_order_data,
            standards=detected_standards,
        )

        elution_orders = generator.generate_elution_orders()

        save_elution_orders(
            elution_orders,
            output_path=output_dir / "Elution_Orders.xlsx",
        )

        print("Step 5: Generating valid combinations")
        processor = ElutionCombinationProcessor(
            elution_orders=elution_orders,
            elution_order_data=elution_order_data,
            standards=detected_standards,
            output_dir=output_dir / "Elution_Results",
        )
        processor.run()

        print("Workflow with standards complete.")

        return {
            "original_data": original_data,
            "mass_filtered_data": mass_filtered_data,
            "detected_standards": detected_standards,
            "updated_mz_dial": updated_mz_dial,
            "elution_order_data": elution_order_data,
            "elution_orders": elution_orders,
        }