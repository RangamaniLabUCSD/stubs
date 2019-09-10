# Functions to help with managing solutions / post-processing
import dolfin as d
import mpi4py.MPI as pyMPI
import numpy as np
import matplotlib.pyplot as plt
import pickle

comm = d.MPI.comm_world
size = comm.size
rank = comm.rank
root = 0


from stubs import unit
#import stubs.model_assembly as model_assembly

# # matplotlib settings
# lwsmall = 1.5
# lwmed = 3
# lineopacity = 0.6
# fsmed = 7
# fssmall = 5



class Data(object):
    def __init__(self, config):
        self.config = config
        self.solutions = {}
        self.errors = {}
        #self.plots = {'solutions': {'fig': plt.figure(), 'subplots': []}}
        self.plots = {'solutions': plt.figure()}
        self.timer = d.Timer()

    def initVTK(self, SD):
        for sp_name, sp in SD.Dict.items():
            self.solutions[sp_name] = {}

            self.solutions[sp_name]['num_species'] = sp.compartment.num_species
            self.solutions[sp_name]['comp_name'] = sp.compartment_name
            self.solutions[sp_name]['comp_idx'] = int(sp.compartment_index)
            self.solutions[sp_name]['concentration_units'] = sp.concentration_units

            file_str = self.config.directory['solutions'] + '/' + sp_name + '.pvd'
            self.solutions[sp_name]['vtk'] = d.File(file_str)

    def storeVTK(self, u, t):
        for sp_name in self.solutions.keys():
            comp_name = self.solutions[sp_name]['comp_name']
            comp_idx = self.solutions[sp_name]['comp_idx']
            if self.solutions[sp_name]['num_species'] == 1:
                self.solutions[sp_name]['vtk'] << (u[comp_name]['u'], t)
            else:
                self.solutions[sp_name]['vtk'] << (u[comp_name]['u'].split()[comp_idx], t)

    def computeStatistics(self, u, t, SD):
        #for sp_name in speciesList:
        for sp_name in SD.Dict.keys():
            comp_name = self.solutions[sp_name]['comp_name']
            comp_idx = self.solutions[sp_name]['comp_idx']

            # compute statistics and append values
            ustats = dolfinGetFunctionStats(u[comp_name]['u'], comp_idx)
            for key, value in ustats.items():
                if key not in self.solutions[sp_name].keys():
                    self.solutions[sp_name][key] = [value]
                else:
                    self.solutions[sp_name][key].append(value)

            # append the time
            if 'tvec' not in self.solutions[sp_name].keys():
                self.solutions[sp_name]['tvec'] = [t]
            else:
                self.solutions[sp_name]['tvec'].append(t)

    def computeError(self, u, comp_name, errorNormKey):
        errorNormDict = {'L2': 2, 'Linf': np.Inf}
        if comp_name not in self.errors.keys():
            self.errors[comp_name] = {}
        #for key in errorNormKeys:
        error_norm = errorNormDict[errorNormKey]
        u_u = u[comp_name]['u'].vector().get_local()
        u_k = u[comp_name]['k'].vector().get_local()
        u_n = u[comp_name]['n'].vector().get_local()
        abs_err = np.linalg.norm(u_u - u_k, ord=error_norm)
        #rel_err = np.linalg.norm((u_u - u_k)/u_n, ord=error_norm)
        rel_err = 1.0
       
        if errorNormKey not in self.errors[comp_name].keys():
            self.errors[comp_name][errorNormKey] = {'rel': [], 'abs': []}
        #     self.errors[comp_name][errorNormKey]['abs'] = [abs_err]
        #     self.errors[comp_name][errorNormKey]['rel'] = [rel_err]
        # else:
        #     self.errors[comp_name][errorNormKey]['abs'].append(abs_err)
        #     self.errors[comp_name][errorNormKey]['rel'].append(rel_err)

        self.errors[comp_name][errorNormKey]['rel'].append(rel_err)
        self.errors[comp_name][errorNormKey]['abs'].append(abs_err)

#            self.errors[comp_name][errorNormKey].append(np.linalg.norm(u[comp_name]['u'].vector().get_local()
#                                    - u[comp_name]['k'].vector().get_local(), ord=error_norm))

    def initPlot(self):
        # NOTE: for now plots are individual; add an option to group species into subplots by category
        numPlots = len(self.solutions.keys())
        subplotCols = 3
        subplotRows = int(np.ceil(numPlots/subplotCols))
        for idx, key in enumerate(self.solutions.keys()):
            self.plots['solutions'].add_subplot(subplotRows,subplotCols,idx+1)


    def plotSolutions(self, plot_settings):
        for idx, key in enumerate(self.solutions.keys()):
            soln =  self.solutions[key]
            subplot = self.plots['solutions'].get_axes()[idx]
            subplot.clear()
            subplot.plot(soln['tvec'], soln['min'], linewidth=plot_settings['linewidth_small'], color='k')
            subplot.plot(soln['tvec'], soln['mean'], linewidth=plot_settings['linewidth_med'], color='k')
            subplot.plot(soln['tvec'], soln['max'], linewidth=plot_settings['linewidth_small'], color='k')

            unitStr = '{:P}'.format(self.solutions[key]['concentration_units'].units)
            subplot = self.plots['solutions'].get_axes()[idx]
            subplot.title.set_text(key)# + ' [' + unitStr + ']')
            subplot.title.set_fontsize(plot_settings['fontsize_med'])
            #self.plots['solutions'].canvas.draw()
            #self.plots['solutions'].show()

        #self.plots['solutions'].tight_layout()
        for ax in self.plots['solutions'].axes:
            ax.ticklabel_format(useOffset=False)
            plt.setp(ax.get_xticklabels(), fontsize=plot_settings['fontsize_small'])
            plt.setp(ax.get_yticklabels(), fontsize=plot_settings['fontsize_small'])
        self.plots['solutions'].savefig(plot_settings['figname'], figsize=(24,24),dpi=300,bbox_inches='tight')

    def outputPickle(self):
        saveKeys = ['tvec','min','mean','max','std']
        newDict = {}
        for sp_name in self.solutions.keys():
            newDict[sp_name] = {}
            for key in saveKeys:
                newDict[sp_name][key] = self.solutions[sp_name][key]

        # pickle file
        with open('solutions_'+self.model_parameters['tag']+'.obj', 'wb') as pickle_file:
            pickle.dump(newDict, pickle_file) 



#    def finalizePlot(self):
#        for idx, key in enumerate(self.solutions.keys()):
#            unitStr = '{:P}'.format(self.solutions[key]['concentration_units'].units)
#            subplot = self.plots['solutions'].get_axes()[idx]
#            subplot.title.set_text(key + ' [' + unitStr + ']')
#            subplot.title.set_fontsize(fsmed)
#        self.plots['solutions'].savefig(self.model_parameters['figName'])





#import matplotlib.pyplot as plt
#import time
#fig = plt.figure()
#fig.show()
#for i in range(10):
#    plt.clf()
#    xlist = list(range(i))
#    ylist = [x**2 for x in xlist]
#    plt.plot(xlist,ylist)
#    time.sleep(0.3)
#
#    fig.canvas.draw()
#
#import matplotlib.pyplot as pylab
#dat=[0,1]
#pylab.plot(dat)
#pylab.ion()
#pylab.draw()
#for i in range (18):
#    dat.append(random.uniform(0,1))
#    pylab.plot(dat)
#    pylab.draw()
#    time.sleep(1)

# ====================================================
# General fenics

# get the values of function u from subspace idx of some mixed function space, V
def dolfin_get_dof_indices(V,species_idx):
    """
    Returned indices are *local* to the CPU (not global)
    function values can be returned e.g.
    indices = dolfin_get_dof_indices(V,species_idx)
    u.vector().get_local()[indices]
    """
    if V.num_sub_spaces() > 1:
        indices = np.array(V.sub(species_idx).dofmap().dofs())
    else:
        indices = np.array(V.dofmap().dofs())
    first_idx, last_idx = V.dofmap().ownership_range() # indices that this CPU owns

    return indices-first_idx # subtract index offset to go from global -> local indices


def reduceVector(u):
    """
    comm.allreduce() only works when the incoming vectors all have the same length. We use comm.Gatherv() to gather vectors
    with different lengths
    """
    rank = d.MPI.comm_world.rank
    sendcounts = np.array(comm.gather(len(u), root)) # length of vectors being sent by workers
    if rank == root:
        print("reduceVector(): CPUs sent me %s length vectors, total length: %d"%(sendcounts, sum(sendcounts)))
        recvbuf = np.empty(sum(sendcounts), dtype=float)
    else:
        recvbuf = None

    comm.Gatherv(sendbuf=u, recvbuf=(recvbuf, sendcounts), root=root)

#    if rank==root:
#        return(recvbuf)
    return recvbuf



def dolfinGetFunctionValues(u,species_idx):
    """
    Returns the values of a VectorFunction. When run in parallel this will *not* double-count overlapping vertices
    which are shared by multiple CPUs (a simple call to u.sub(species_idx).compute_vertex_values() will do this though...)
    """
    V = u.function_space()
    indices = dolfin_get_dof_indices(V,species_idx)
    uvec = u.vector().get_local()[indices]
    return uvec

# when run in parallel, some vertices are shared by multiple CPUs. This function will return all the function values on
# the invoking CPU. Note that summing/concatenating the results from this function over multiple CPUs will result in
# double-counting of the overlapping vertices!
#def dolfinGetFunctionValuesParallel(u,idx):
#    uvec = u.sub(idx).compute_vertex_values()
#    return uvec


def dolfinGetFunctionValuesAtPoint(u, coord, species_idx=None):
    """
    Returns the values of a dolfin function at the specified coordinate 
    :param dolfin.function.function.Function u: Function to extract values from
    :param tuple coord: tuple of floats indicating where in space to evaluate u e.g. (x,y,z)
    :param int species_idx: index of species
    :return: list of values at point. If species_idx is not specified it will return all values
    """
    if species_idx:
        return u(coord)[species_idx]
    else:
        return u(coord)

# def dolfinSetFunctionValues(u,unew,V,idx):
#     # unew can be a scalar (all dofs will be set to that value), a numpy array, or a list
#     dofmap = dolfinGetDOFmap(V,idx)
#     u.vector()[dofmap] = unew


def dolfinSetFunctionValues(u,unew,species_idx):
    """
    unew can either be a scalar or a vector with the same length as u
    """
    V = u.function_space()
    if type(unew) != float:
        assert len(u)==len(unew)
    elif any([type(unew) == x for x in [float, int]]):
        pass
    else:
        raise Exception("unew must be either a scalar or vector with the same length as u!")

    indices = dolfin_get_dof_indices(V, species_idx)
    uvec = u.vector()
    values = uvec.get_local()
    values[indices] = unew

    uvec.set_local(values)
    uvec.apply('insert')


def dolfinGetFunctionStats(u,species_idx):
    V = u.function_space()
    uvalues = dolfinGetFunctionValues(u,species_idx)
    return {'mean': uvalues.mean(), 'min': uvalues.min(), 'max': uvalues.max(), 'std': uvalues.std()}

#def dolfinGetF

def dolfinFindClosestPoint(mesh, coords):
    """
    Given some point and a mesh, returns the coordinates of the nearest vertex
    """
    p = d.Point(coords)
    L = list(d.vertices(mesh))
    distToVerts = [np.linalg.norm(p.array() - x.midpoint().array()) for x in L]
    minDist = min(distToVerts)
    minIdx = distToVerts.index(minDist) # returns the local index (wrt the cell) of the closest point

    closestPoint = L[minIdx].midpoint().array()

    if size > 1:
        min_dist_global, min_idx = comm.allreduce((minDist,rank), op=pyMPI.MINLOC)

        if rank == min_idx:
            comm.Send(closestPoint, dest=root)

        if rank == root:
            comm.Recv(closestPoint, min_idx)
            print("CPU with rank %d has the closest point to %s: %s. The distance is %s" % (min_idx, coords, closestPoint, min_dist_global))
            return closestPoint, min_dist_global
    else:
        return closestPoint, minDist


