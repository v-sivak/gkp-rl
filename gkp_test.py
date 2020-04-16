# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 15:13:49 2020

@author: Vladimir Sivak
"""

import os
os.environ["TF_MIN_GPU_MULTIPROCESSOR_COUNT"]="2"
os.environ["TF_FORCE_GPU_ALLOW_GROWTH"]='true'
os.environ["CUDA_VISIBLE_DEVICES"]="1"


import tensorflow as tf
import gkp_helper_functions as hf
import gkp_tf_env_wrappers as wrappers

from gkp.gkp_tf_env.gkp_tf_env import GKP
from gkp.gkp_tf_env import policy as plc





env = GKP(init='vac', H=1, batch_size=1, episode_length=50, 
          reward_mode = 'stabilizers', quantum_circuit_type='v3')

import action_script_Baptiste_8round as action_script
policy = plc.ScriptedPolicyV2(env.time_step_spec(), action_script)


### Plot cardinal points
if 0:
    for state_name in env.states.keys():
        state = tf.reshape(env.states[state_name], [1,env.N])
        hf.plot_wigner_tf_wrapper(state, title=state_name)


### Simulate one episode
if 1:
    time_step = env.reset()
    policy_state = policy.get_initial_state(env.batch_size)
    while not time_step.is_last()[0]:
        action_step = policy.action(time_step, policy_state)
        policy_state = action_step.state
        time_step = env.step(action_step.action)
        hf.plot_wigner_tf_wrapper(env.info['psi_cached'], 
                                  title=str(env._elapsed_steps))
    # hf.plot_wigner_tf_wrapper(env.info['psi_cached'])




