from . import *
from toybox.testing.models.openai_baselines import getModel
from toybox.testing.envs.gym import get_turtle
from toybox.interventions.breakout import BreakoutIntervention
from baselines.common.vec_env.vec_frame_stack import VecFrameStack
from baselines.common.cmd_util import make_vec_env
import tensorflow as tf

class PPO2(Agent):

    def __init__(self, toybox: Toybox, seed=1234, withstate=None):
        super().__init__(toybox, seed=seed)

        nenv = 1
        frame_stack_size = 4
        env_type = 'atari'
        env_id = 'BreakoutToyboxNoFrameskip-v4'
        family='ppo2'
 
        # Nb: OpenAI special cases acer, trpo, and deepQ.
        env = VecFrameStack(make_vec_env(env_id, env_type, nenv, seed) , frame_stack_size)
        turtle = get_turtle(env)
        turtle.toybox.set_seed(seed)
        obs = env.reset()
        if withstate: turtle.toybox.write_state_json(withstate)

        model_path = 'agents/data/BreakoutToyboxNoFrameskip-v4.regress.model'
        model = getModel(env, family, seed, model_path)
        
        self.model = model
        self.env = env
        self.turtle = turtle
        self.obs = obs
        self.tfsession = tf.Session(graph=tf.Graph()).__enter__()

    def __del__(self):
        # EMT (25/05/2020)
        # Knowing how context managers are *supposed* to work, this is how
        # proper exiting of the context manager *should* be written:
        #
        # self.tfsession.__exit__(None, None, None)        
        #
        # HOWEVER, tensorflow clearly passes around information here, so 
        # when we execute the above, the session isn't properly cleaned up.
        # THIS IS A HACK
        try:
            self.tfsession.__exit__(True, True, None)
        except: pass

    def get_action(self):
        action = self.model.step(self.obs)[0]
        obs, _, done, info = self.env.step(action)
        self.obs = obs
        ale_action = self.toybox.get_legal_action_set()[action[0]]
        # Frameskip workaround
        self.toybox.write_state_json(self.turtle.toybox.state_to_json())
        return int(ale_action) if not done else None
