from io import BytesIO

import ipywidgets as widgets
import pandas as pd
from IPython.display import clear_output, display

from .workflow import MS1Workflow


def _load_uploaded_file(upload_widget):
    """
    Load a CSV or Excel file from an ipywidgets FileUpload widget.
    """
    uploaded_file = list(upload_widget.value.values())[0]
    file_name = uploaded_file["metadata"]["name"]
    file_content = uploaded_file["content"]

    if file_name.endswith(".xlsx"):
        return pd.read_excel(BytesIO(file_content))

    if file_name.endswith(".csv"):
        return pd.read_csv(BytesIO(file_content))

    raise ValueError("Unsupported file format. Please upload a .csv or .xlsx file.")


class MS1WorkflowWidget:
    """
    Notebook interface for running the MS1 workflow.

    Supports:
    - workflow without standards
    - workflow with standards
    """

    def __init__(self):
        self.mode = widgets.Dropdown(
            options=[
                ("Without standards", "without_standards"),
                ("With standards", "with_standards"),
            ],
            value="without_standards",
            description="Mode:",
        )

        self.mz_dial_upload = widgets.FileUpload(
            accept=".xlsx,.csv",
            multiple=False,
            description="mzDial File",
        )

        self.standard_upload = widgets.FileUpload(
            accept=".xlsx,.csv",
            multiple=False,
            description="Standards File",
        )

        self.ppm_threshold = widgets.IntText(
            value=10,
            description="PPM:",
            layout=widgets.Layout(width="220px"),
        )

        self.rt_order_tolerance = widgets.FloatText(
            value=0.01,
            description="RT order tol:",
            layout=widgets.Layout(width="260px"),
        )

        self.rt_alignment_tolerance = widgets.FloatText(
            value=0.01,
            description="RT align tol:",
            layout=widgets.Layout(width="260px"),
        )

        self.run_button = widgets.Button(
            description="Run workflow",
            button_style="success",
        )

        self.output = widgets.Output()

        self.mode.observe(self._on_mode_change, names="value")
        self.run_button.on_click(self._on_run_clicked)

        self._on_mode_change(None)

    def display(self):
        """
        Display the notebook widget interface.
        """
        display(
            widgets.VBox(
                [
                    widgets.HTML("<h3>MS1-Based Workflow</h3>"),
                    self.mode,
                    widgets.Label("Upload mzDial results:"),
                    self.mz_dial_upload,
                    self.standard_upload,
                    self.ppm_threshold,
                    self.rt_order_tolerance,
                    self.rt_alignment_tolerance,
                    self.run_button,
                    self.output,
                ]
            )
        )

    def _on_mode_change(self, _):
        """
        Show or hide standards-specific widgets depending on selected mode.
        """
        if self.mode.value == "with_standards":
            self.standard_upload.layout.display = ""
            self.rt_alignment_tolerance.layout.display = ""
        else:
            self.standard_upload.layout.display = "none"
            self.rt_alignment_tolerance.layout.display = "none"

    def _on_run_clicked(self, _):
        """
        Run the selected workflow mode.
        """
        with self.output:
            clear_output()

            if not self.mz_dial_upload.value:
                print("Please upload an mzDial file.")
                return

            if self.mode.value == "with_standards" and not self.standard_upload.value:
                print("Please upload a standards file.")
                return

            try:
                mz_dial_data = _load_uploaded_file(self.mz_dial_upload)

                workflow = MS1Workflow(
                    ppm_threshold=self.ppm_threshold.value,
                    rt_order_tolerance=self.rt_order_tolerance.value,
                    rt_alignment_tolerance=self.rt_alignment_tolerance.value,
                    output_dir="outputs",
                )

                if self.mode.value == "with_standards":
                    standards = _load_uploaded_file(self.standard_upload)
                    workflow.run_with_standards(
                        mz_dial_data=mz_dial_data,
                        standards=standards,
                    )
                else:
                    workflow.run_without_standards(
                        mz_dial_data=mz_dial_data,
                    )

                print("\nDone. Results saved in the outputs folder.")

            except Exception as error:
                print(f"Error: {error}")