import logging, os
from pathlib import (
    Path,
)
from typing import (
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    Any
)

import dpdata
import numpy as np
from dargs import (
    Argument,
    ArgumentEncoder,
    Variant,
    dargs,
)
from dflow.python import (
    OP,
    OPIO,
    Artifact,
    BigParameter,
    FatalError,
    OPIOSign,
    TransientError,
)

from dpgen2.constants import (
    fp_default_log_name,
    fp_default_out_data_name,
)
from dpgen2.utils.run_command import (
    run_command,
)

from .prep_fp import (
    PrepFp,
)
from .run_fp import (
    RunFp,
)
from .vasp_input import (
    VaspInputs,
    make_kspacing_kpoints,
)

# global static variables
vasp_conf_name = "POSCAR"
gpaw_input_name = "gpaw_runfile"


class GpawInputs:
    def __init__(
            self,
            gpaw_runfile: os.PathLike = "gpaw_singlepoint.py"):
        self.gpaw_runfile = gpaw_runfile

    @staticmethod
    def args() -> List[Argument]:
        """The arguments of the Gpaw class."""
        return [
            Argument(
                "gpaw_runfile", os.PathLike, optional=True, default="gpaw_singlepoint.py", doc="Input file to run GPAW.",
            )
        ]

    @staticmethod
    def normalize_config(data={}, strict=True):
        ta = GpawInputs.args()
        base = Argument("base", dict, ta)
        data = base.normalize_value(data, trim_pattern="_*")
        base.check_value(data, strict=strict)
        return data


class PrepGpaw(PrepFp):
    def prep_task(
        self,
        conf_frame: dpdata.System,
        gpaw_inputs: GpawInputs,
    ):
        """Define how one Vasp task is prepared.

        Parameters
        ----------
        conf_frame : dpdata.System
            One frame of configuration in the dpdata format.
        gpaw_inputs : GpawInputs
            The GpawInputs object handels all other input files of the task.
        """

        conf_frame.to("vasp/poscar", vasp_conf_name)
        Path(gpaw_input_name).symlink_to(gpaw_inputs.gpaw_runfile)  # create a file "gpaw_runfile" that is a symlink to "gpaw_singlepoint.py"


class RunGpaw(RunFp):
    def input_files(self) -> List[str]:
        """The mandatory input files to run a vasp task.

        Returns
        -------
        files: List[str]
            A list of madatory input files names.

        """
        return [vasp_conf_name, gpaw_input_name]

    def optional_input_files(self) -> List[str]:
        r"""The optional input files to run a vasp task.

        Returns
        -------
        files: List[str]
            A list of optional input files names.

        """
        return []

    def run_task(
        self,
        command: str,
        out: str,
        log: str,
    ) -> Tuple[str, str]:
        r"""Defines how one FP task runs

        Parameters
        ----------
        command : str
            The command of running vasp task
        out : str
            The name of the output data file.
        log : str
            The name of the log file

        Returns
        -------
        out_name: str
            The file name of the output data in the dpdata.LabeledSystem format.
        log_name: str
            The file name of the log.
        """

        log_name = log
        out_name = out
        ### run gpaw
        command = " ".join([command, ">", log_name])
        ret, out, err = run_command(command, shell=True)
        if ret != 0:
            logging.error(
                "".join(
                    ("GPAW failed\n", "out msg: ", out, "\n", "err msg: ", err, "\n")
                )
            )
            raise TransientError("GPAW failed")
        ### convert the output to deepmd/npy format
        sys = dpdata.LabeledSystem("CONF_ASE.traj", fmt="ase/traj")
        sys.to("deepmd/npy", out_name)
        return out_name, log_name

    @staticmethod
    def args():
        """The argument definition of the `run_task` method.

        Returns
        -------
        arguments: List[dargs.Argument]
            List of dargs.Argument defines the arguments of `run_task` method.
        """

        doc_gpaw_cmd = "The command of GPAW"
        doc_gpaw_log = "The log file name of GPAW"
        doc_gpaw_out = "The output dir name of labeled data. In `deepmd/npy` format provided by `dpdata`."
        return [
            Argument("command", str, optional=True, default="gpaw python", doc=doc_gpaw_cmd),
            Argument("out", str, optional=True, default=fp_default_out_data_name, doc=doc_gpaw_out,),
            Argument("log", str, optional=True, default=fp_default_log_name, doc=doc_gpaw_log),
        ]
