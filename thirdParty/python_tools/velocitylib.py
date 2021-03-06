#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Contains functions to perform 2-D velocity calculations for various elements.

Also defines an Element, backwards compatible "vormat" style object.

AUTHOR - Jarrad Kapor (jarrad.kapor@postgrad.curtin.edu.au)
MODIFIED - 2009.11

"""

import array
import math
import os

try:
    import velocitymodule
except ImportError:
    print "velocitymodule import error, regenerating files now..."
    os.system("cd ../../cfmm_2d.git; make clean; make -j4; cd ../python_tools.git")
    import velocitymodule

DEFAULT_ASSUME_POINT_LENGTH = 32

def lamb_vortex_vel(vort_x, vort_y, vort_str, vort_core_size_sqrd,
                    eval_point_x, eval_point_y, threads=4, fmm=True,
                    fmm_accuracy=0.0001, fmm_targetsperbox=15,):

    """Generic solver for all types of problems involving the influences of a singular vortex on a point in 2d space.
    
    NOTES       
        Positive vorticity is clockwise.
        All inputs/outputs must be single column vectors
        u = horizontal velocity at point (evalPointX,evalPointY)
        v = vertical velocity at point (evalPointX,evalPointY)
        vortX = x-position of the discrete vortex
        vortY = y-position of the discrete vortex
        vortStr = strength of the discrete vortex
        vortCoreSizeSqrd = lamb vortex core size squared (use 0 if is a point vortex)
        evalPointX = x-position to evaluate velocity
        evalPointY = y-position to evaluate velocity
        opt_threads = 4 (number of threads to use)
        opt_accuracy= 0.0001 (approximately p=13, can directly input p value)
        opt_nofmm = 0 (1 means dont use the full FMM)
        opt_targetsperbox = 15 (criteria for an oversized fmm box)

    """
    # FMM likes lists only! 
    if not hasattr(vort_x, '__len__'):
        vort_x = [vort_x]
        vort_y = [vort_y]
        vort_str = [vort_str]
        vort_core_size_sqrd = [vort_core_size_sqrd]
    if not hasattr(eval_point_x, '__len__'):
        eval_point_x = [eval_point_x]
        eval_point_y = [eval_point_y]
   
    out_u = make_similar_sequence(eval_point_x)
    out_v = make_similar_sequence(eval_point_x)
    if not fmm:
        # turn off far field approximations
        fmm_accuracy = -1.0; 
        
    velocitymodule.lamb_vortex(vort_x, vort_y, vort_str, vort_core_size_sqrd, eval_point_x, eval_point_y, out_u, out_v, threads, fmm_accuracy, fmm_targetsperbox,)

    return (out_u, out_v)

def lamb_vortex_vort(vort_x, vort_y, vort_str, vort_core_size_sqrd,
                    eval_point_x, eval_point_y, threads=4, fmm=True,
                    fmm_accuracy=0.0001, fmm_targetsperbox=15,):

    """Generic solver for all types of problems involving the influences of a singular vortex on a point in 2d space.
    
    NOTES       
        Positive vorticity is clockwise.
        All inputs/outputs must be single column vectors
        u = vorticity at point (evalPointX,evalPointY)
        vortX = x-position of the discrete vortex
        vortY = y-position of the discrete vortex
        vortStr = strength of the discrete vortex
        vortCoreSizeSqrd = lamb vortex core size squared (use 0 if is a point vortex)
        evalPointX = x-position to evaluate velocity
        evalPointY = y-position to evaluate velocity
        opt_threads = 4 (number of threads to use)
        opt_accuracy= 0.0001 (approximately p=13, can directly input p value)
        opt_nofmm = 0 (1 means dont use the full FMM)
        opt_targetsperbox = 15 (criteria for an oversized fmm box)

    """
    
    # FMM likes lists only! 
    if not hasattr(vort_x, '__len__'):
        vort_x = [vort_x]
        vort_y = [vort_y]
        vort_str = [vort_str]
        vort_core_size_sqrd = [vort_core_size_sqrd]
    if not hasattr(eval_point_x, '__len__'):
        eval_point_x = [eval_point_x]
        eval_point_y = [eval_point_y]
    
    out_u = make_similar_sequence(eval_point_x)
    out_v = make_similar_sequence(eval_point_x)
    if not fmm:
        # turn off far field approximations, hasnt been properly implemented in C yet...
        fmm_accuracy = 1000; 
        
    velocitymodule.lamb_vortex_vort(vort_x, vort_y, vort_str, vort_core_size_sqrd,
                                eval_point_x, eval_point_y, out_u, out_v,
                                threads, fmm_accuracy, fmm_targetsperbox,)
    # out_u really returns scalar vorticity
    return (out_u, out_v)

def lamb_vortex_vel_python(x, y, s, c, ex, ey):
    """Generic solver for all types of problems involving the influences of a singular vortex on a point in 2d space. Python Implementation
    
    NOTES       
        Positive vorticity is clockwise.
        All inputs/outputs must be single column vectors
        u = horizontal velocity at point (evalPointX,evalPointY)
        v = vertical velocity at point (evalPointX,evalPointY)
        vortX = x-position of the discrete vortex
        vortY = y-position of the discrete vortex
        vortStr = strength of the discrete vortex
        vortCore = lamb vortex core size squared (use 0 if is a point vortex)
        evalPointX = x-position to evaluate velocity
        evalPointY = y-position to evaluate velocity
    """
    if not hasattr(x, '__len__'):
        x = [x]
        y = [y]
        s = [s]
        c = [c]
    if not hasattr(ex, '__len__'):
        ex = [ex]
        ey = [ey]

    num_targets = len(ex)
    u_vel = []
    v_vel = []

    for j in xrange(num_targets):
        total_u = 0.0
        total_v = 0.0
        for i in xrange(len(x)):
            rel_y 	= ey[j] - y[i]
            rel_x 	= ex[j] - x[i]
            r_sqrd = rel_y ** 2 + rel_x ** 2

            if (r_sqrd > 0.0): 
                vel = s[i] / (2.0 * math.pi * r_sqrd)
                sigSqr	= c[i] ** 2
                if sigSqr > 0.0:
                    #	Is a lamb vortex where the evaluation point is located inside
                    #	the core
                    coreCorr = 1.0 - math.exp(-r_sqrd / sigSqr)
                    vel *= coreCorr
            
            else:
                vel = 0.0

            total_u += rel_y * vel
            total_v -= rel_x * vel

        u_vel.append(total_u)
        v_vel.append(total_v)
    
    return (u_vel, v_vel)

def vortex_element_vel(xl, yl, strl, xr, yr, strr, eval_point_x, eval_point_y, threads=4, fmm=True, fmm_accuracy=9, fmm_targetsperbox=5, panel_tolerance=1e-3, assume_point_length=DEFAULT_ASSUME_POINT_LENGTH, is_infinite_sheet=False):
    
    """Solves the velocity induced by many(or 1) constant/linear strength vortex\
        elements on a point in 2d space.

    # NOTES       : Positive vorticity is clockwise,
    # : All inputs/outputs must be single column vectors
    # USAGE       :   u = horizontal velocity at point (evalx,evaly)
    # :   v = vertical velocity at point (evalx,evaly)
    # :   xl = x-position of left end of sheet
    # :   yl = y-position of left end of sheet
    # :   strl = strength per metre, at left end of sheet
    # :   xr = x-position of right end of sheet
    # :   yr = y-position of right end of sheet
    # :   strr = strength per metre, at right end of sheet
    # :   evalx = x-position to evaluate velocity
    # :   evaly = y-position to evaluate velocity
    # GLOBAL OPTS :   opt_threads = 4 (number of threads to use)
    # :   fmm_accuracy = (!!!!! not yet!!!) min times panel length away for farfield approximations
    # :   fmm = True or False for far field approximations
    # :   opt_targetsperbox = 5 (criteria for an oversized fmm box)
    # --------------:
    panel_tolerance = percentage of panel length away from panel that code assumes evaluation point is on top of the panel
    ie panel_tolerance = 1e100000 presumes all evaluation points would be ontop of the panel
    ie panel_tolerance = 0.0 lets the machine precision determine if we are above/below or on the panel == bug making material
    assumePointLength = number of panel lengths away required before panel can be treated as a source (basically restricts the max fmm level)
    
    """
    
    out_u = make_similar_sequence(eval_point_x)
    out_v = make_similar_sequence(eval_point_x)
    if not fmm:
        # turn off far field approximations
        fmm_accuracy = -1.0
    
    velocitymodule.vortex_element(xl, yl, strl, xr, yr, strr, eval_point_x, eval_point_y, out_u, out_v, threads, fmm_accuracy, fmm_targetsperbox, panel_tolerance, assume_point_length, is_infinite_sheet)

    return (out_u, out_v)


def source_element_vel(xl, yl, strl, xr, yr, strr, eval_point_x, eval_point_y, threads=4, fmm=True, fmm_accuracy=9, fmm_targetsperbox=5, panel_tolerance=1e-3, assume_point_length=DEFAULT_ASSUME_POINT_LENGTH):
    """This is a generic solver for the velocity induced by many(or 1)\
        constant/linear strength source/sink elements on a point in 2d space.
    
    This just wraps the vortex_element_vel function, see its help thread for\
    more information. 
    """

    (out_uv, out_vv) = vortex_element_vel( xl, yl, strl, xr, yr, strr, eval_point_x, eval_point_y, threads=threads, fmm=fmm, fmm_accuracy=fmm_accuracy, fmm_targetsperbox=fmm_targetsperbox, panel_tolerance=panel_tolerance, assume_point_length=assume_point_length)
    out_u = [-i for i in out_vv]
    out_v = out_uv
    return (out_u, out_v)

def sortex_element_vel(xl, yl, sourcestr, xr, yr, vortstr, eval_point_x, eval_point_y, threads=4, fmm=True, fmm_accuracy=9, fmm_targetsperbox=5, panel_tolerance=1e-3, assume_point_length=DEFAULT_ASSUME_POINT_LENGTH):
    """This is a generic solver for the velocity induced by many(or 1)\
        constant/linear strength source/sink - vortex elements on a point in 2d space.
    
    This just wraps the vortex_element_vel and source_element_vel function, see its help thread for\
    more information. 
    """

    (vout_uv, vout_vv) = vortex_element_vel( xl, yl,vortstr, xr, yr,vortstr, eval_point_x, eval_point_y, threads=threads, fmm=fmm, fmm_accuracy=fmm_accuracy, fmm_targetsperbox=fmm_targetsperbox, panel_tolerance=panel_tolerance, assume_point_length=assume_point_length)
    
    (sout_uv, sout_vv) = source_element_vel( xl, yl,sourcestr, xr, yr,sourcestr, eval_point_x, eval_point_y, threads=threads, fmm=fmm, fmm_accuracy=fmm_accuracy, fmm_targetsperbox=fmm_targetsperbox, panel_tolerance=panel_tolerance, assume_point_length=assume_point_length )
    out_u = [vout_uv[i] + sout_uv[i] for i in xrange(len(vout_vv))]
    out_v = [vout_vv[i] + sout_vv[i] for i in xrange(len(vout_vv))]
    return (out_u, out_v)

def vortex_sheet_vel( xl, yl, xr, yr, strr, eval_point_x, eval_point_y, threads=4,):
    """Solves the velocity induced by many(or 1) semi-infinite vortex sheets in\
        2d space.

    # NOTES       : Positive vorticity is clockwise,
    # : All inputs/outputs must be single column vectors
    # USAGE       :   u = horizontal velocity at point (evalx,evaly)
    # :   v = vertical velocity at point (evalx,evaly)
    # :   xl = x-position of left end of sheet
    # :   yl = y-position of left end of sheet
    # :   xr = x-position of right end of sheet
    # :   yr = y-position of right end of sheet
    # :   strr = strength per metre of the semi-infinite sheet
    # :   evalx = x-position to evaluate velocity
    # :   evaly = y-position to evaluate velocity
    # MARKSNOTES    :
    # Influence due to Semi-Infinite Vortex sheets with POINT VORTICES
    #
    # Induced velocity field in the x-direction:
    #
    # NOTE: This was achieved through the integration and subsequent
    # summation of eq. 3.30 and 3.31.  (These equations are exactly
    # the same as eqns 3.28 and 3.29 but with circulation expressed
    # as a per length quantity and integrated along the length of the
    # sheet).

    """
    # dont need to pass anything else, as none of it will be used for seminfinites anyways
    (out_u, out_v) = vortex_element_vel( xl, yl, strr, xr, yr, strr, eval_point_x, eval_point_y, threads=threads, is_infinite_sheet=True)
    return (out_u, out_v)

def vortex_el_n_sheet_vel(panXLa, panYLa, panStrla, panXRa, panYRa, panStrra,evalXa,evalYa, IS_INF_SHEET=False):
    # sheet vel validated to matlab on 11/2009

    sign = lambda x: float((x >= 0.0) - (x < 0.0)) 
    
    num_targets = len(evalXa)
    uVel = []
    vVel = []
    ZERO = 0.0
    if IS_INF_SHEET:
        REL_TOL = 0.0
    else:
        REL_TOL = 0.0
    
    for j in xrange(num_targets):
        total_u = 0.0
        total_v = 0.0
        evalX = evalXa[j]
        evalY = evalYa[j]
        for i in xrange(len(panXLa)):
            panXL = panXLa[i]
            panYL = panYLa[i]
            panXR = panXRa[i]
            panYR = panYRa[i]
            strPerM = panStrla[i]
            strR = panStrra[i]
            strL = panStrla[i]
            
            panLen = math.sqrt((panYR-panYL) ** 2 + (panXR-panXL) ** 2)
            TOLERENCE = REL_TOL * panLen
            if not (((abs(evalX - panXL) < TOLERENCE) and (abs(evalY-panYL)<TOLERENCE)) or ((abs(evalX-panXR) <TOLERENCE) and (abs(evalY -panYR)<TOLERENCE))):
                if panLen > 0:
                    panCenX = (panXL+panXR)/2.0
                    panCenY = (panYL+panYR)/2.0
                    
                globalXRel = (evalX - panCenX)
                globalYrel = (evalY - panCenY)
                #// alpha in terms of katz and plotkins terminoligy
                cosAlpha = (panXR - panXL) / panLen
                sinAlpha = (panYL - panYR) / panLen

                #convert to local panel coordinates relative to the panel!
                # Calculate the relative x and y distances from element "j"
                #   page 318 in katz and plotkins transformation matrices.
                xRel = globalXRel* cosAlpha - globalYrel* sinAlpha
                yRel = globalXRel* sinAlpha + globalYrel* cosAlpha

                xlRel = xRel - (-panLen/2.0)
                xrRel = xRel - (panLen/2.0)
             
                if IS_INF_SHEET:
                    if (yRel == 0.0):
                        uP = 0.0
                    else:
                        #thetaPanL = math.atan2(yRel, xlRel)
                        #thetaPanR = math.atan2(yRel, xrRel)
                        thetaPanL = math.atan(xlRel / yRel)
                        thetaPanR = math.atan(xrRel / yRel)
                        #print "sign yReal", yRel, "is ", sign(yRel)
                        uP = 1.0*(strPerM / (2.0*math.pi)) * (math.pi * sign(yRel) + thetaPanR - thetaPanL)
                else: 
                    thetaPanR = math.atan2(yRel , xrRel)
                    thetaPanL = math.atan2(yRel , xlRel)                    
                    uP = 1.0*(strPerM / (2.0*math.pi)) * (thetaPanR - thetaPanL)

                rRightSqrd = xrRel ** 2 + yRel ** 2
                rLeftSqrd = xlRel ** 2 + yRel ** 2
                if IS_INF_SHEET:
                   vP = (strPerM / (4.0*math.pi)) * math.log(rLeftSqrd / rRightSqrd)
                else:
                   vP = (strPerM / (4.0*math.pi)) * math.log(rRightSqrd / rLeftSqrd)
                
                # Done constant panel bit, now for the linear gradient...if there is one...dont care if its a sheet as already set sl=sr, so grad=0
                
                strGradient = (strR - strL) / panLen
                if (abs(strGradient) > ZERO):
                    # do extra Linear panel calculations too
                    # see k&p eq 10.72 page.279 and/or eq10.48 p269
                    uP += (strGradient / (2*math.pi)) * ( yRel * math.log(rRightSqrd / rLeftSqrd) / 2.0 + xlRel * (thetaPanR - thetaPanL))
                    vP += (strGradient / (2*math.pi)) * ( xlRel * math.log(rRightSqrd / rLeftSqrd) / 2.0 + yRel * (thetaPanL - thetaPanR) + panLen )

               #   convert from panel coords back to global coords
                total_u += uP* cosAlpha + vP* sinAlpha;
                total_v += -uP* sinAlpha + vP* cosAlpha;
        uVel.append(total_u)
        vVel.append(total_v)

    return (uVel, vVel)

vortex_sheet_vel_python = lambda xl, yl, xr, yr, strr, eval_point_x, eval_point_y: vortex_el_n_sheet_vel( xl, yl,strr, xr, yr, strr, eval_point_x, eval_point_y, True)
vortex_element_vel_python = lambda xl, yl, sl, xr, yr, sr, eval_point_x, eval_point_y: vortex_el_n_sheet_vel( xl, yl, sl, xr, yr, sr, eval_point_x, eval_point_y)

def make_similar_sequence(example_sequence):
    tmp_seq = [0.0] * len(example_sequence)
    if isinstance(example_sequence, list):

    # want output as list also

        out_seq = tmp_seq
    else:

    # return as a numpy array
    # out_seq = numpy.zeros(len(exampleSequence))

        out_seq = array.array('d', tmp_seq)
    return out_seq


class Elemat: 
    """Creates an object that acts like a dictionary, but can be referenced like an array

    Great for use with old code to keep backwards compatability.

    Example use:
        vormat_values = [ x, y, s, c]
        vormat_labels = ['x', 'y', 's', 'c']
        vormat = Elemat(vormat_values, vormat_labels)

    Now both notations work and are equivalent...
        vx = vormat[0] 
            == 
        vx = vormat['x']
        
        vormat[0] = nvx
            ==
        vormat['x'] = nvx

    Also you can add labels after creation...but thats not tested fully yet...
    Note: slices dont work yet. and theres no print function yet...

    """ 
    def __init__(self, values, keys=None): 
        self.data = values
        self.aliases = {}
        self.prev_u_data = None
        self.prev_v_data = None
        for i in xrange(len(values)): 
            # Point the key to a hash. 
            self.aliases[i] = i 
            if keys is not None:
                # Point the alias to the same hash as the real key. 
                self.aliases[keys[i]] = i
            
    def setalias(self, key, alias): 
        # Point the alias to the same hash as the real key. 
        self.aliases[alias] = hash(key)

    def getnumfields(self): 
        return len(self.data)

    def moment(self, mom_num, ex=0.0, ey=0.0):
        """Returns 0th and 1st moments"""
        str = self.__getitem__('s')
        x = self.__getitem__('x')
        y = self.__getitem__('y')
        if mom_num == 0:
            mom_ret_x = sum(str)
            ret_val = mom_ret_x
        elif mom_num == 1:
            mom_ret_x = sum((str[i] * (x[i] - ex) for i in xrange(len(str))))
            mom_ret_y = sum((str[i] * (y[i] - ey) for i in xrange(len(str))))
            ret_val = mom_ret_x, mom_ret_y
        else:
            raise ValueError('moment ' + str(mom_num) + ' not implemented')

        return ret_val
    
    def len(self):
        return len(self.data[0])
    
    def x(self, inds=None):
        ret_val = self.__getitem__('x')
        if inds is not None:
            ret_val = self.cherry_pick(ret_val, inds)
        return ret_val
    def y(self, inds=None):
        ret_val = self.__getitem__('y')
        if inds is not None:
            ret_val = self.cherry_pick(ret_val, inds)
        return ret_val
    def s(self, inds=None):
        ret_val = self.__getitem__('s')
        if inds is not None:
            ret_val = self.cherry_pick(ret_val, inds)
        return ret_val
    def c(self, inds=None):
        ret_val = self.__getitem__('c')
        if inds is not None:
            ret_val = self.cherry_pick(ret_val, inds)
        return ret_val
    def prev_u(self):
        return self.prev_u_data
    def prev_v(self):
        return self.prev_v_data
    def prev_vels(self):
        return (self.prev_u(), self.prev_v())

    def set_prev_vels(self, in_u, in_v):
        self.prev_u_data = in_u
        self.prev_v_data = in_v

    def add_particle(self, in_x,in_y,in_s,in_c):
        """Add a single particle"""
        self.x().append(in_x)
        self.y().append(in_y)
        self.s().append(in_s)
        self.c().append(in_c)
        if self.prev_u() is not None:
            self.prev_u().append(None)
            self.prev_v().append(None)   
    
    def add_particles(self, in_x,in_y,in_s,in_c):
        """Add a single particle"""
        self.x().extend(in_x)
        self.y().extend(in_y)
        self.s().extend(in_s)
        self.c().extend(in_c)
        if self.prev_u() is not None:
            self.prev_u().extend([None]* len(in_x))
            self.prev_v().extend([None]* len(in_x))

    def delete_vorts(self, inds):
        """Deletes an array of vortices from vormat"""
        # need to delete in reverse order otherwise indices arents correct!
        inds.sort()
        inds.reverse()
        val_list = []
        val_list.append(self.x())
        val_list.append(self.y())
        val_list.append(self.s())
        val_list.append(self.c())
        if self.prev_u() is not None:
            val_list.append(self.prev_u())
            val_list.append(self.prev_v())

        for data_val in val_list:
            for i in inds:
                del data_val[i]

    def __getitem__(self, key): 
        return self.data[self.aliases[key]]

    def __setitem__(self, key, value): 
        self.data[self.aliases[key]] = value 
    
    def __str__(self): 
        ret_str = str()
        for i in xrange(len(self.data[0])):
            tmpstr = '|\t'
            for j in xrange(len(self.data)-1):
                tmpstr += str(self.data[j][i]) + '\t'
            tmpstr += str(self.data[-1][i]) + '\t' 

            tmpstr += '|\n'
            ret_str += tmpstr
        
        return ret_str           

    @staticmethod
    def cherry_pick(data, inds):
        return [data[inds[i]] for i in xrange(len(inds))]

def memleaktest():
    import random
    import pdb
    n = 100
    m = 10000

    x = [1*random.random() for i in xrange(m)]
    y = [1*random.random() for i in xrange(m)]
    s = [0*random.random() for i in xrange(m)]
    c = [0*random.random() for i in xrange(m)]
    ex = x
    ey = y

    for i in xrange(n):
        print i
        [u,v] = lamb_vortex_vel(x,y,s,c,ex,ey)
        
    pdb.set_trace()

    
def main():
    '''callup different test suites'''
    memleaktest()

if __name__ == '__main__':
    main()
