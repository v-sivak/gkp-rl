# -*- coding: utf-8 -*-
"""
Created on Mon May  4 14:30:36 2020

@author: Vladimir Sivak
"""
import qutip as qt
import tensorflow as tf
from numpy import sqrt, pi
from gkp.gkp_tf_env.gkp_tf_env import GKP
from tensorflow import complex64 as c64
from tensorflow.keras.backend import batch_dot

class OscillatorQubitGKP(GKP):
    """
    This class inherits simulation-independent functionality from the GKP
    class and implements simulation by including the qubit in the Hilbert
    space and using gate-based approach to quantum circuits.
    
    """
    
    def __init__(self, **kwargs):
        self.tensorstate = True
        super(OscillatorQubitGKP, self).__init__(**kwargs)

    def define_operators(self):
        """
        Define all relevant operators as tensorflow tensors of shape [2N,2N].
        We adopt the notation in which qt.basis(2,0) is a ground state
        Methods need to take care of batch dimension explicitly. 
        
        """
        N = self.N
        # Create qutip tensors
        I = qt.tensor(qt.identity(2), qt.identity(N))
        a = qt.tensor(qt.identity(2), qt.destroy(N))
        a_dag = qt.tensor(qt.identity(2), qt.create(N))
        q = (a.dag() + a) / sqrt(2)
        p = 1j*(a.dag() - a) / sqrt(2)
        n = qt.tensor(qt.identity(2), qt.num(N))
        
        sz = qt.tensor(qt.sigmaz(), qt.identity(N))
        sx = qt.tensor(qt.sigmax(), qt.identity(N))
        sm = qt.tensor(qt.sigmap(), qt.identity(N))
        hadamard = qt.tensor(qt.qip.operations.snot(), qt.identity(N))
        
        P = {0 : qt.tensor(qt.ket2dm(qt.basis(2,0)), qt.identity(N)),
             1 : qt.tensor(qt.ket2dm(qt.basis(2,1)), qt.identity(N))}

        Kerr = -1/2 * (2*pi) * self.K_osc * n * n 
        dispersive = -1/2 * (2*pi) * self.chi * sz * n
        Hamiltonian = Kerr # + dispersive    # TODO: include dispersive
                                             # TODO: include other channels
        c_ops = [sqrt(1/self.T1_osc)*a] #,       # photon loss
              #   sqrt(1/self.T1_qb)*sm,       # qubit decay
            #     sqrt(0.5/self.Tphi_qb)*sz]   # qubit dephasing

        
        # Convert to tensorflow tensors
        self.I = tf.constant(I.full(), dtype=c64)
        self.a = tf.constant(a.full(), dtype=c64)
        self.a_dag = tf.constant(a_dag.full(), dtype=c64)
        self.q = tf.constant(q.full(), dtype=c64)
        self.p = tf.constant(p.full(), dtype=c64)
        self.sz = tf.constant(sz.full(), dtype=c64)
        self.sx = tf.constant(sx.full(), dtype=c64)
        self.sm = tf.constant(sm.full(), dtype=c64)
        self.hadamard = tf.constant(hadamard.full(), dtype=c64)
        
        P = {i : tf.constant(P[i].full(), dtype=c64) for i in [0,1]}
        self.P = {i : tf.stack([P[i]]*self.batch_size) for i in [0,1]}
        
        self.Hamiltonian = tf.constant(Hamiltonian.full(), dtype=c64)
        self.c_ops = [tf.constant(op.full(), dtype=c64) for op in c_ops]  
        
        
    @tf.function
    def quantum_circuit_v1(self, psi, action):
        """
        Apply sequenct of quantum gates version 1. In this version conditional 
        translation by 'beta' is not symmetric (translates if qubit is in '1') 
        
        Input:
            action -- dictionary of batched actions. Dictionary keys are
                      'alpha', 'beta', 'phi'
            
        Output:
            psi_final -- batch of final states; shape=[batch_size,N]
            psi_cached -- batch of cached states; shape=[batch_size,N]
            obs -- measurement outcomes; shape=(batch_size,)
            
        """
        # extract parameters
        alpha = self.vec_to_complex(action['alpha'])
        beta = self.vec_to_complex(action['beta'])
        phi = action['phi']
        
        # execute gates
        psi = self.mc_sim_delay.run(psi)
        psi_cached = batch_dot(self.translate(alpha), psi)
        psi = self.mc_sim_round.run(psi_cached)
        psi = self.normalize(psi)
        psi, obs = self.phase_estimation(psi, beta, angle=phi, sample=True)
        
        # flip qubit conditioned on the measurement
        sx = tf.stack([self.sx]*self.batch_size)
        psi_final = psi * tf.cast((obs == 1), c64) \
            + batch_dot(sx, psi) * tf.cast((obs == -1), c64)

        return psi_final, psi_cached, obs
    

    @tf.function
    def phase_estimation(self, psi, beta, angle, sample=False):
        """
        One round of phase estimation. 
        
        Input:
            psi -- batch of state vectors; shape=[batch_size,2N]
            beta -- translation amplitude. shape=(batch_size,)
            angle -- angle along which to measure qubit. shape=(batch_size,)
            sample -- bool flag to sample or return expectation value
        
        Output:
            psi -- batch of collapsed states if sample==True, otherwise same 
                   as input psi; shape=[batch_size,2N]
            z -- batch of measurement outcomes if sample==True, otherwise
                 batch of expectation values of qubit sigma_z.
                 
        """
        CT = self.ctrl(self.translate(beta))
        Phase = self.ctrl(self.phase(angle)*self.I)
        Hadamard = tf.stack([self.hadamard]*self.batch_size)
        
        psi = batch_dot(Hadamard, psi)
        psi = batch_dot(CT, psi)
        psi = batch_dot(Phase, psi)
        psi = batch_dot(Hadamard, psi)
        psi = self.normalize(psi)
        return self.measurement(psi, self.P, sample=sample)

    

    @tf.function
    def ctrl(self, U):
        """
        Batch controlled-U gate. Applies 'U' if qubit is '1', and identity if 
        qubit is '1'.
        
        Input:
            U -- unitary on the oscillator subspace written in the combined 
                 qubit-oscillator Hilbert space; shape=[batch_size,2N,2N]
        
        """
        return self.P[0] + batch_dot(self.P[1], U)
    