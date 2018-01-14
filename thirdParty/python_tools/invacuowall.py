#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Testing wall invacuo

AUTHOR - Jarrad Kapor (jarrad.kapor@postgrad.curtin.edu.au)
MODIFIED - 2009.08

"""
import time
import math
import pylab
import pdb
from misctools import where_am_i

def main():
    # create a wall to use
    mode=6
    numnodes = 25
    total_timesteps_mult = 1
    dt = 10.005
    L = 1.0
    dx = L / (numnodes-1)
    # print 'ratio', dt / (dx**2)
    k = 0.0*1*(2*math.pi)**2
    h = L / 100.0
    rho = 100
    m = rho * h
    q = 0.0*1.0
    pre_tension = 0*10*(2*math.pi)**2 /( (mode * math.pi / L) ** 2)

    IS_NON_LIN = False

    vp = 0.5
    B_no_E = h ** 3 / (12 * (1 - vp ** 2))
    E = 0.01*((2*math.pi)**2 /( (1 * math.pi / L) ** 4)) / B_no_E
    B = B_no_E * E
    w_force = [-0*9.81]*numnodes
    init_amp = h * 5/ mode
    n_x_pos = [dx * i for i in xrange(numnodes)]

    boundconds = 1
    MAX_ERROR = 1e-3
    MAX_ITERS = 10
    STEP_METHODs = ['euler', 'mod-pred-corr', 'adams-bashforth']
    # adams doesnt work yet...need to set initial conditions with a euler at 0...
    STEP_METHOD = STEP_METHODs[1]
    wall_properties = {'E':E, 'h':h, 'vp':vp, 'q':q, 'k':k, 'L':L,
                       'pre_tension':pre_tension, 'dx':dx, 'mass_per_m':m,
                       'IS_NON_LIN':IS_NON_LIN, 'boundconds':boundconds, 'nonlin_q':0}
    numerical_dict = {'MAX_ERROR':MAX_ERROR, 'MAX_ITERS':MAX_ITERS, 
                      'STEP_METHOD':STEP_METHOD, 'safe_ratio':3,
                      'numsubsteps':1 }
    xax = [0,L]
    yay = [-init_amp, init_amp]
    plot_dict = {}
    plot_dict['xax'] = xax 
    plot_dict['yay'] = yay 

    # theoretical calculation from the natural frequency by applying 
    # W0sin(npiwt/L)e^(iwt) to the differential equation
    mode_freq = lambda n: math.sqrt((B * (n * math.pi / L) ** 4 + 
                                    pre_tension * (n * math.pi / L) ** 2 + 
                                    k ) / m) / (2 * math.pi)
    first_mode_freq = mode_freq(1)
    last_mode_freq = mode_freq(numnodes-1)
    noise_freq = 1/dt
    noise_to_mode = noise_freq / last_mode_freq
    # numerical noise generated by the 1/dt must no coincide with a natural frequency
    MIN_NOISE_LAST = 3
    if noise_to_mode < MIN_NOISE_LAST:
        print 'noise to last mode ratio of', noise_freq/last_mode_freq, '...bad things happen for <', MIN_NOISE_LAST
        print '!!resetting dt to something more sane!'
        dt = 1/(MIN_NOISE_LAST*last_mode_freq)
        noise_freq = 1/dt
        noise_to_mode = noise_freq / last_mode_freq
    
    print 'first modal frequency', first_mode_freq
    print 'this modal frequency', mode_freq(mode)
    print 'last modal frequency', last_mode_freq
    print 'forcing frequency of the noise', noise_freq
    print 'noise to last mode ratio of', noise_freq/last_mode_freq, '...bad things happen for <', MIN_NOISE_LAST
    print 'novaks ratio', dt/(dx**2)

    y=raw_input('enter to continue')

    w_pos = [0.0] * numnodes
    w_vel = None
    #timestep
    w_log_pos = L/(2*mode)
    w_log_pos_num = int(w_log_pos/dx)
    w_log = []
    w_pos[0] = 0
    w_accel = None
    
    pylab.ion()
    pylab.figure()
    pylab.hold(False)
    pylab.grid(True)
    pylab.draw()
 
    w_pos = init_wall(init_amp, n_x_pos, mode)
    max_lin_err = []
    max_lin_err.append(calc_max_error_in_linear_ass(w_pos, n_x_pos))
    print 'init linear error','%.3f' % (max_lin_err[-1] * 100), '%' 
    pylab.plot(n_x_pos, w_pos, 'ro', 
                n_x_pos, w_pos, 'b-.', 
                xax, yay,'w.',
                [n_x_pos[w_log_pos_num]], [w_pos[w_log_pos_num]], 'gx',
                [n_x_pos[w_log_pos_num]]*2, yay, 'g-.')
    pylab.axis('equal')
    pylab.draw() 
    time.sleep(1)    
    
    total_timesteps = total_timesteps_mult * int(1 / ( first_mode_freq * dt))
    tt = total_timesteps
    for t in xrange(tt):
        w_pos, w_vel, w_accel, tot_iters, rms_error = advance_wall_by_dt(dt, n_x_pos, w_pos, w_vel, w_accel, w_force, wall_properties, numerical_dict, plot_dict)
        
        print 't', t * dt, 'total iters', tot_iters, 'with converge error','%.2f' % (rms_error * 100), '%',
        max_lin_err.append(calc_max_error_in_linear_ass(w_pos, n_x_pos))
        print 'and linear error','%.2f' % (max_lin_err[-1] * 100), '%'
        w_log.append(w_pos[w_log_pos_num])
    print 'first modal frequency', first_mode_freq
    print 'this modal frequency', mode_freq(mode)
    print 'last modal frequency', last_mode_freq
    print 'forcing frequency of the noise', noise_freq
    print 'noise to last mode ratio of', noise_freq/last_mode_freq, '...bad things happen for <', MIN_NOISE_LAST
    print 'novaks ratio', dt/(dx**2)
   
    pylab.axis('auto')
    pylab.plot([i*dt for i in xrange(tt)], w_log, 'rx')

    pylab.ioff()
    y=raw_input('enter to continue')
    

def advance_wall_by_dt(dt, n_x_pos, w_pos, w_vel, w_accel, w_force, wall_properties, numerical_dict, plot_dict=None):
    """wrapper fuction to advancing a wall by dt. Ensures convergence safety with sub-stepping"""
    
    # determine a much safer dt!
    numsubsteps = numerical_dict['numsubsteps']
    safe_dt = dt / numsubsteps
    force_log = []
    tot_tot_iters = 0
    tot_rms_error = 0
    for i in xrange(numsubsteps):
        # w_force assumed constant throughout!
        (w_pos, w_vel, w_accel, tot_iters, rms_error, this_force_log) = do_advance_wall_by_dt(safe_dt, n_x_pos, w_pos, w_vel, w_accel, w_force, wall_properties, numerical_dict, plot_dict=None)
        tot_rms_error += rms_error
        tot_tot_iters += tot_iters
        force_log.append(this_force_log)
    
    return w_pos, w_vel, w_accel, tot_tot_iters, rms_error, force_log
    
    

def do_advance_wall_by_dt(dt, n_x_pos, w_pos, w_vel, w_accel, w_force, wall_properties, numerical_dict, plot_dict=None):
    """Advances wall by dt...presumes dt is safe for problem"""

    MAX_ERROR = numerical_dict['MAX_ERROR']
    MAX_ITERS = numerical_dict['MAX_ITERS'] 
    STEP_METHOD = numerical_dict['STEP_METHOD']
    numnodes = len(n_x_pos)
    if w_vel is None:
        # cant use multistep method yet as this is first call
        STEP_METHOD = 'euler'
        w_vel = [0.0] * numnodes
        w_accel = [0.0] * numnodes

    # beginning solving now
    w_converged = False
    if STEP_METHOD == 'euler':
        # plain euler
        w_vel_old = [w_vel[i] for i in xrange(numnodes)]
        w_pos_old = [w_pos[i] for i in xrange(numnodes)]
    elif STEP_METHOD == 'mod-pred-corr':
        # predictor corrector model
        w_vel_old = [w_vel[i] + dt * w_accel[i] / 2.0 for i in xrange(numnodes)]
        w_pos_old = [w_pos[i] + dt * w_vel[i] / 2.0 for i in xrange(numnodes)]
    elif STEP_METHOD == 'adams-bashforth':
        w_vel_old = [w_vel[i] - dt * w_accel[i] / 2.0 for i in xrange(numnodes)]
        w_pos_old = [w_pos[i] - dt * w_vel[i] / 2.0 for i in xrange(numnodes)]
    else:
        raise ValueError("Given wall/FEM time stepping method \"" + str(STEP_METHOD) + "\" does not exist!")

    tot_iters = 0
    while not w_converged:
        tot_iters += 1
        w_accel_prev = w_accel
        w_vel_prev = w_vel
        w_pos_prev = w_pos

        w_accel, force_log = get_accel(w_pos, w_vel, w_force, n_x_pos, wall_properties)
        if STEP_METHOD == 'euler':
            w_vel = [w_vel_old[i] + dt * w_accel[i] for i in xrange(numnodes)]
            w_pos = [w_pos_old[i] + dt * w_vel[i] for i in xrange(numnodes)]
        elif STEP_METHOD == 'mod-pred-corr':
            w_vel = [w_vel_old[i] + dt * w_accel[i] / 2.0 for i in xrange(numnodes)]
            w_pos = [w_pos_old[i] + dt * w_vel[i] / 2.0 for i in xrange(numnodes)]
        elif STEP_METHOD == 'adams-bashforth':
            w_vel_old = [w_vel_old[i] + 1.5 * dt * w_accel[i] for i in xrange(numnodes)]
            w_pos_old = [w_pos_old[i] + 1.5 * dt * w_vel[i] for i in xrange(numnodes)]
        else:
            raise ValueError("Given time stepping method \"" + str(STEP_METHOD) + "\" does not exist!")

        if plot_dict is not None: 
            xax = plot_dict['xax']
            yay = plot_dict['yay']
            pylab.plot(n_x_pos, w_pos, 'ro', n_x_pos, w_pos, 'b-.', xax, yay,'w.')
            pylab.draw()
        
        if False:
            pylab.plot(n_x_pos, w_accel, 'ro', hold=False)
            pylab.draw()        
            pylab.savefig(str(i) + '.png')

        diff_sqrd = [(w_pos[i] - w_pos_prev[i])**2 for i in xrange(numnodes)]
        tot_sqrd = [i ** 2 for i in w_pos]
        if sum(tot_sqrd) != 0.0:
            rms_error = math.sqrt(sum(diff_sqrd)/sum(tot_sqrd))
        else:
            rms_error = 0.0

        if rms_error < MAX_ERROR or tot_iters >= MAX_ITERS :
            w_converged = True
            if tot_iters >= MAX_ITERS:
                raise FloatingPointError("Wall motion didn't converge in " +
                                         str(MAX_ITERS) + " iterations, maybe you should try using (more) wall time sub-steps (reduce novaks safe ratio), or maybe even your damping value provides the most sicnifigant force, hence we will never be able to converge on V in our way?")

    return w_pos, w_vel, w_accel, tot_iters, rms_error, force_log

def get_accel(w_pos, w_vel, w_force, n_x_pos, wall_properties):
    E = wall_properties['E']
    h = wall_properties['h']
    vp = wall_properties['vp']
    q = wall_properties['q']
    nonlin_q = wall_properties['nonlin_q']

    k = wall_properties['k']
    L = wall_properties['L']
    pre_tension = wall_properties['pre_tension']
    dx = wall_properties['dx']
    mass_per_m = wall_properties['mass_per_m']
    IS_NON_LIN = wall_properties['IS_NON_LIN']
    boundconds = wall_properties['boundconds']
    
    num_els = len(w_pos)
    force_external = [-w_force[i] for i in xrange(num_els)]
    force_spring = [-k * w_pos[i] for i in xrange(num_els)]
    force_damping = [-q * w_vel[i] for i in xrange(num_els)]
    d1_dx1 = dn_dxn(w_pos, n_x_pos,1)
    d2_dx2 = dn_dxn(w_pos, n_x_pos,2)
    d4_dx4 = dn_dxn(w_pos, n_x_pos,4)
    dq1_dx1 = dn_dxn(w_vel, n_x_pos,1)

    P = pre_tension
    if IS_NON_LIN:
        delta_L = sum(((math.sqrt(1 + (d1_dx1[i] ** 2)) - 1) * dx 
                       for i in xrange(num_els)))
        P += E * h / (1 - vp ** 2) * (delta_L / L)

    force_tension = [P * d2_dx2[i] for i in xrange(num_els)]
    
    B = E * h ** 3 / (12 * (1 - vp ** 2))
    force_bending = [- B * d4_dx4[i] for i in xrange(num_els)]
    force_nonlin_q = [- nonlin_q * dq1_dx1[i] for i in xrange(num_els)]

    total_w_force = [force_external[i] + force_bending[i] + force_tension[i] + force_spring[i] + force_damping[i] + force_nonlin_q[i] for i in xrange(num_els)]
    mass_per_element = mass_per_m * dx          # dont need to know exact length as stretch would vary density! mass must be constant!
    w_accel = [i / mass_per_m for i in total_w_force]

    the_force_log = {"force_external":force_external, "force_bending":force_bending, "force_tension":force_tension, "force_spring":force_spring, "force_damping":force_damping, "total_w_force":total_w_force,'force_nonlin_q':force_nonlin_q}
    enforce_boundaryconds(w_accel, boundconds)
    if False:
        pylab.figure()
        pylab.plot(n_x_pos, w_pos, 'r.', n_x_pos, d1_dx1, 'b.', n_x_pos, d2_dx2, 'g.', n_x_pos, d4_dx4,'k.')
    
    return w_accel, the_force_log

def dn_dxn(w_pos, n_x_pos, order):
    # using 5th order method from bickley        
    diff_dict = {
                1: lambda i: (-8 * (w_pos[i-1] - w_pos[i+1]) +
                              1 * (w_pos[i-2] - w_pos[i+2])) / (12 * dx),
                2: lambda i: (-30 * w_pos[i] + 
                              16 * (w_pos[i-1] + w_pos[i+1]) -
                              1 * (w_pos[i-2] + w_pos[i+2])) / (12 * dx ** 2),
                4: lambda i: (6 * w_pos[i] - 
                              4 * (w_pos[i-1] + w_pos[i+1]) +
                              1 * (w_pos[i-2] + w_pos[i+2])) / (dx ** 4)
                }

    diff_eq = diff_dict[order]
    dx = n_x_pos[1] - n_x_pos[0]
    
    # setup hinged end dummy points
    w_pos = [-w_pos[2], -w_pos[1]] + w_pos + [-w_pos[-2] , -w_pos[-3]]
    dn_dxn = [diff_eq(i) for i in xrange(2,len(w_pos)-2)]
    
    return dn_dxn

def init_wall(amp, x_pos, mode):
    L = x_pos[-1] - x_pos[0] 
    pertfun = lambda x,L: amp * math.sin(mode*2*math.pi*x/(2*L))
    w_pos = [pertfun(x_pos[i], L) for i in xrange(len(x_pos))]
    w_pos[-1]=0.0
    return w_pos

def enforce_boundaryconds(w_accel, boundconds):
    if boundconds == 1:
        # two fixed ends
        w_accel[0] = 0.0
        w_accel[-1] = 0.0
    else:
        raise TypeError('ooops wrong BCS')

def calc_max_error_in_linear_ass(w_pos, n_x_pos):
    #d1_dx1 corresponds to tanTheta
    max_grad = max([abs(i) for i in dn_dxn(w_pos, n_x_pos, 1)])
    max_error = 0.0
    if max_grad != 0.0:
        max_error = 1 - max_grad / math.atan(max_grad)

    return max_error


def nat_freq(wall_properties, mode):
    E = wall_properties['E']
    h = wall_properties['h']
    vp = wall_properties['vp']
    q = wall_properties['q']
    k = wall_properties['k']
    L = wall_properties['L']
    pre_tension = wall_properties['pre_tension']
    dx = wall_properties['dx']
    m = wall_properties['mass_per_m']
    IS_NON_LIN = wall_properties['IS_NON_LIN']
    boundconds = wall_properties['boundconds']
    B = E * h ** 3 / (12 * (1 - vp ** 2))

    n = mode
    #mode_freq = math.sqrt((B * (n * math.pi / L) ** 4 + pre_tension * (n * math.pi / L) ** 2 + k ) / m) / (2 * math.pi)
    mode_freq = (n * math.pi)**2 * math.sqrt(B / (m * (L ** 4))) / (2 * math.pi)
    return mode_freq

if __name__ == '__main__':
    main()