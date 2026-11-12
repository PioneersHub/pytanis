"""Some helper functions for HiGHS (https://highs.dev/)

`pyomo` and `highspy` need to be installed, consider `pip install 'pytanis[all]'`.

ToDo:
    * Introduce a function `check_model_vars` that checks the names of variables and sets to be alphanumeric
      before reading in a solution in `set_solution_from_file`.
"""

import re
from collections.abc import Iterator

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers import Highs
from pyomo.core.base.PyomoModel import ConcreteModel


def _pyomo_name_to_mps_name(pyomo_name: str) -> str:
    """Replicate Pyomo's symbolic_solver_labels MPS encoding.

    Pyomo encodes vbSchedule[a, b, 'c d'] as vbSchedule(a_b__c_d_) in MPS files:
      '[' -> '('
      ']' -> ')'
      characters in {',', ' ', "'"} -> '_'
    """
    result = pyomo_name.replace('[', '(').replace(']', ')')
    result = re.sub(r"[, ']", '_', result)
    return result


def _build_mps_to_pyomo_map(model: ConcreteModel) -> dict[str, str]:
    """Build a lookup table: MPS-encoded variable name -> Pyomo variable name.

    This is necessary because Pyomo's symbolic_solver_labels encoding is not
    unambiguously reversible (underscores collide with encoded separators).
    Building the map forward from Pyomo objects is exact by construction.
    """
    mapping = {}
    for v in model.component_data_objects(pyo.Var, active=True):
        mapping[_pyomo_name_to_mps_name(v.name)] = v.name
    return mapping


def read_sol_file(file_name: str) -> Iterator[tuple[str, float]]:
    """Read a solution file from HiGHS solver with default output style.

    Yields (mps_encoded_name, value) pairs exactly as they appear in the file.
    Use _build_mps_to_pyomo_map to translate to Pyomo variable names.
    """
    line_re = re.compile(r'(.+?)(_binary_indicator_var)?\s+([\d.e+-]+)$')

    with open(file_name, encoding='utf8') as fh:
        while True:
            line = fh.readline()
            if line.startswith('# Columns'):
                break
        for line in fh.readlines():
            if line.startswith('#'):
                break
            stripped = line.strip()
            if not stripped:
                continue
            match_obj = line_re.match(stripped)
            if match_obj is None:
                msg = f'Could not interpret line: {line}'
                raise RuntimeError(msg)
            var_name, binary, val = match_obj.groups()
            val = float(val)
            binary = binary.replace('_', '.', 1) if binary else ''
            yield f'{var_name}{binary}', val


def set_solution_from_file(model: ConcreteModel, file_name: str):
    """Given a HiGHS solution file set the variables of a Pyomo model accordingly.

    This is a workaround to set a Pyomo model's variables to the solution
    from a HiGHS solution file. Handles complex variable names with special
    characters (spaces, quotes, nested parentheses) produced by Pyomo's
    symbolic_solver_labels encoding.
    """
    # Initialize via HiGHS to set up internal solver state (variable order may be wrong)
    opt = Highs()
    opt.set_instance(model)
    opt._solver_model.readSolution(file_name, 0)
    opt._sol = opt._solver_model.getSolution()
    opt.load_vars()

    # Build exact MPS-name -> Pyomo-name mapping from model objects (not regex)
    mps_to_pyomo = _build_mps_to_pyomo_map(model)

    # Read sol file (keys are MPS-encoded names)
    file_sol_mps = dict(read_sol_file(file_name))

    # Translate to Pyomo names
    file_sol = {mps_to_pyomo.get(k, k): v for k, v in file_sol_mps.items()}

    # Overwrite variable values using symbolic names from the file
    for v, ref_info in opt._referenced_variables.items():
        using_cons, using_sos, using_obj = ref_info
        if using_cons or using_sos or (using_obj is not None):
            var = opt._vars[v][0]
            var.set_value(file_sol[var.name], skip_validation=True)
