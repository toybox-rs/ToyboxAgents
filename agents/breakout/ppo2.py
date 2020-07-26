from . import *
from toybox.testing.models.openai_baselines import getModel
from toybox.testing.envs.gym import get_turtle
from toybox.interventions.breakout import BreakoutIntervention
from baselines.common.vec_env.vec_frame_stack import VecFrameStack
from baselines.common.cmd_util import make_vec_env
import tensorflow as tf

class PPO2(BreakoutAgent):

    def __init__(self, toybox: Toybox, *args, withstate=None, model_path='agents/data/BreakoutToyboxNoFrameskip-v4.regress.model', **kwargs):
        # The action_repeat value comes from the skip argument of 
        # MaxAndSkipEnv in atari_wrappers.py
        # Setting this back to 1 from 4 because I think it messes up some
        # of our reasoning.
        super().__init__(toybox, *args, action_repeat=4, **kwargs)

        nenv = 1
        frame_stack_size = 4
        env_type = 'atari'
        env_id = 'BreakoutToyboxNoFrameskip-v4'
        family = 'ppo2'
 
        # Nb: OpenAI special cases acer, trpo, and deepQ.
        env = VecFrameStack(make_vec_env(env_id, env_type, nenv, self.seed), frame_stack_size)
        turtle = get_turtle(env)
        turtle.toybox.set_seed(self.seed)
        obs = env.reset()
        if withstate: turtle.toybox.write_state_json(withstate)

        model = getModel(env, family, self.seed, model_path)

        self.model = model
        self.env = env
        self.turtle = turtle
        self.obs = obs
        self.done = False
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

    def stopping_condition(self, maxsteps):
        return super().stopping_condition(maxsteps) or self.done

    def reset(self, seed=None):
        super().reset(seed=seed)
        self.done = False
        turtle = get_turtle(self.env)
        turtle.toybox.new_game()
        if seed: turtle.toybox.set_seed(seed)
        self.obs = self.env.reset()
        self.tfsession.__del__()
        self.tfsession = tf.Session(graph=tf.Graph()).__enter__()

    def get_action(self):
        action = self.model.step(self.obs)[0]
        obs, _, done, info = self.env.step(action)
        done = done[0]
        self.obs = obs
        self.done = done
        ale_action = self.toybox.get_legal_action_set()[action[0]]
        # Frameskip workaround
        self.toybox.write_state_json(self.turtle.toybox.state_to_json())
        return int(ale_action) if not done else None
