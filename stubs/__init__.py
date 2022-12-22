"""
stubs
"""
# Add imports here
# import config first
from . import config
from . import data_manipulation
from . import model_assembly
from . import solvers
from . import model
from . import common
from . import mesh


import pint

unit = pint.UnitRegistry()
unit.define("molecule = mol/6.022140857e23")
unit.define("nM_10 = 10*nM")
unit.define("nM_100 = 100*nM")
unit.define("uM_10 = 10*uM")
unit.define("uM_100 = 100*uM")
unit.define("molec_10_per_um2 = 10*molecule/um**2")
unit.define("molec_100_per_um2 = 100*molecule/um**2")
unit.define("molec_1000_per_um2 = 1000*molecule/um**2")
unit.define("molec_div10_per_um2 = 1/10*molecule/um**2")
unit.define("molec_div100_per_um2 = 1/100*molecule/um**2")
unit.define("molec_div1000_per_um2 = 1/1000*molecule/um**2")

__all__ = [
    "config",
    "data_manipulation",
    "model_assembly",
    "solvers",
    "model",
    "common",
    "mesh",
]
