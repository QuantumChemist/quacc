"""Core recipes for Gaussian"""
from __future__ import annotations

import multiprocessing
from typing import TYPE_CHECKING

from ase.calculators.gaussian import Gaussian

from quacc import fetch_atoms, job
from quacc.runners.calc import run_calc
from quacc.schemas.cclib import cclib_summarize_run
from quacc.utils.dicts import merge_dicts

if TYPE_CHECKING:
    from ase import Atoms

    from quacc.schemas.cclib import cclibSchema

LOG_FILE = f"{Gaussian().label}.log"
GEOM_FILE = LOG_FILE


@job
def static_job(
    atoms: Atoms | dict,
    charge: int,
    spin_multiplicity: int,
    xc: str = "wb97x-d",
    basis: str = "def2-tzvp",
    calc_swaps: dict | None = None,
    copy_files: list[str] | None = None,
) -> cclibSchema:
    """
    Carry out a single-point calculation.

    ??? Note

        Calculator Defaults:

        ```python
        {
            "mem": "16GB",
            "chk": "Gaussian.chk",
            "nprocshared": multiprocessing.cpu_count(),
            "xc": xc,
            "basis": basis,
            "charge": charge,
            "mult": spin_multiplicity,
            "sp": "",
            "scf": ["maxcycle=250", "xqc"],
            "integral": "ultrafine",
            "nosymmetry": "",
            "pop": "CM5",
            "gfinput": "",
            "ioplist": ["6/7=3", "2/9=2000"],
        }
        ```

    Parameters
    ----------
    atoms
        Atoms object or a dictionary with the key "atoms" and an Atoms object as
        the value
    charge
        Charge of the system.
    spin_multiplicity
        Multiplicity of the system.
    xc
        Exchange-correlation functional
    basis
        Basis set
    calc_swaps
        Dictionary of custom kwargs for the calculator.
    copy_files
        Files to copy to the runtime directory.

    Returns
    -------
    cclibSchema
        Dictionary of results, as specified in [quacc.schemas.cclib.cclib_summarize_run][]
    """

    defaults = {
        "mem": "16GB",
        "chk": "Gaussian.chk",
        "nprocshared": multiprocessing.cpu_count(),
        "xc": xc,
        "basis": basis,
        "charge": charge,
        "mult": spin_multiplicity,
        "sp": "",
        "scf": ["maxcycle=250", "xqc"],
        "integral": "ultrafine",
        "nosymmetry": "",
        "pop": "CM5",
        "gfinput": "",
        "ioplist": ["6/7=3", "2/9=2000"],  # see ASE issue #660
    }
    return _base_job(
        atoms,
        charge=charge,
        spin_multiplicity=spin_multiplicity,
        defaults=defaults,
        calc_swaps=calc_swaps,
        additional_fields={"name": "Gaussian Static"},
        copy_files=copy_files,
    )


@job
def relax_job(
    atoms: Atoms,
    charge: int,
    spin_multiplicity: int,
    xc: str = "wb97x-d",
    basis: str = "def2-tzvp",
    freq: bool = False,
    calc_swaps: dict | None = None,
    copy_files: list[str] | None = None,
) -> cclibSchema:
    """
    Carry out a geometry optimization.

    ??? Note

        Calculator Defaults:

        ```python
        {
            "mem": "16GB",
            "chk": "Gaussian.chk",
            "nprocshared": multiprocessing.cpu_count(),
            "xc": xc,
            "basis": basis,
            "charge": charge,
            "mult": spin_multiplicity,
            "opt": "",
            "pop": "CM5",
            "scf": ["maxcycle=250", "xqc"],
            "integral": "ultrafine",
            "nosymmetry": "",
            "freq": "" if freq else None,
            "ioplist": ["2/9=2000"],
        }
        ```

    Parameters
    ----------
    atoms
        Atoms object or a dictionary with the key "atoms" and an Atoms object as
        the value
    charge
        Charge of the system.
    spin_multiplicity
        Multiplicity of the system.
    xc
        Exchange-correlation functional
    basis
        Basis set
    freq
        If a frequency calculation should be carried out.
    calc_swaps
        Dictionary of custom kwargs for the calculator.
    copy_files
        Files to copy to the runtime directory.

    Returns
    -------
    cclibSchema
        Dictionary of results, as specified in [quacc.schemas.cclib.cclib_summarize_run][]
    """

    defaults = {
        "mem": "16GB",
        "chk": "Gaussian.chk",
        "nprocshared": multiprocessing.cpu_count(),
        "xc": xc,
        "basis": basis,
        "charge": charge,
        "mult": spin_multiplicity,
        "opt": "",
        "pop": "CM5",
        "scf": ["maxcycle=250", "xqc"],
        "integral": "ultrafine",
        "nosymmetry": "",
        "freq": "" if freq else None,
        "ioplist": ["2/9=2000"],  # ASE issue #660
    }
    return _base_job(
        atoms,
        charge=charge,
        spin_multiplicity=spin_multiplicity,
        defaults=defaults,
        calc_swaps=calc_swaps,
        additional_fields={"name": "Gaussian Relax"},
        copy_files=copy_files,
    )


def _base_job(
    atoms: Atoms | dict,
    charge: int,
    spin_multiplicity: int,
    defaults: dict | None = None,
    calc_swaps: dict | None = None,
    additional_fields: dict | None = None,
    copy_files: list[str] | None = None,
) -> cclibSchema:
    """
    Base job function for carrying out Gaussian recipes.

    Parameters
    ----------
    atoms
        Atoms object or a dictionary with the key "atoms" and an Atoms object as
        the value
    charge
        Charge of the system.
    spin_multiplicity
        Multiplicity of the system.
    defaults
        Default parameters for the calculator.
    calc_swaps
        Dictionary of custom kwargs for the calculator.
    additional_fields
        Additional fields to supply to the summarizer.
    copy_files
        Files to copy to the runtime directory.

    Returns
    -------
    cclibSchema
        Dictionary of results, as specified in [quacc.schemas.cclib.cclib_summarize_run][]
    """
    atoms = fetch_atoms(atoms)
    flags = merge_dicts(defaults, calc_swaps)

    atoms.calc = Gaussian(**flags)
    atoms = run_calc(atoms, geom_file=GEOM_FILE, copy_files=copy_files)

    return cclib_summarize_run(
        atoms,
        LOG_FILE,
        charge_and_multiplicity=(charge, spin_multiplicity),
        additional_fields=additional_fields,
    )
