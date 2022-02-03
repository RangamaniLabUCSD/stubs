"""
Configuration settings for simulation: plotting, reaction types, solution output, etc.
"""
import dolfin as d
import logging

class Config:
    """
    Refactored config 
         - directories
         - plot settings
         - reactions 
         - logging
    """
    def __init__(self):
        self.solver             = {'final_t': None,
                                   'use_snes': True,
                                   'initial_dt': None,
                                   'adjust_dt': None,
                                   'dt_decrease_factor': 1.0,
                                   'dt_increase_factor': 1.0,}

        # initialize with default values
        self.flags              = {'store_solutions': True,
                                   'allow_unused_components': False}

        self.directory          = {'solutions': 'solutions',
                                   'plots': 'plots'}

        self.output_type        =  'xdmf'

        self.plot_settings      = {'lineopacity': 0.6,
                                   'linewidth_small': 0.6,
                                   'linewidth_med': 2.2,
                                   'fontsize_small': 3.5,
                                   'fontsize_med': 4.5,
                                   'figname': 'figure'}

        #self.probe_plot         = {'A': [(0.5,0.0), (1.0,0.0)]}
        self.probe_plot         = {}

        self.reaction_database  = {'prescribed': 'k',
                                   'prescribed_linear': 'k*u',
                                   'prescribed_leak': 'k*(1-u/umax)'}
        
        self.loglevel           = {'FFC': 'DEBUG',
                                   'UFL': 'DEBUG',
                                   'dijitso': 'DEBUG',
                                   'dolfin': 'INFO'}
        
        self._loglevel_to_int   = {'CRITICAL': 50,
                                   'ERROR': 40,
                                   'WARNING': 30,
                                   'INFO': 20,
                                   'DEBUG': 10,
                                   'NOTSET': 0,}
        

    def check_config_validity(self):
        valid_filetypes = ['xdmf', 'vtk', None]
        if self.output_type not in valid_filetypes:
            raise ValueError(f"Only filetypes: '{valid_filetypes}' are supported.")
        
        if self.solver['final_t'] is None:
            raise ValueError(f"Please provide a final time in config.solver")
        if self.solver['initial_dt'] is None:
            raise ValueError(f"Please provide an initial time-step size in config.solver")

    def set_logger_levels(self):
        # set for dolfin
        d.set_log_level(self._loglevel_to_int[self.loglevel['dolfin']])
        # set for others
        other_loggers = list(self.loglevel.keys())
        other_loggers.remove('dolfin')
        for logger_name in other_loggers:
            logging.getLogger(logger_name).setLevel(self.loglevel[logger_name])
