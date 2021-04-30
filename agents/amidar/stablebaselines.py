import gym
from gym import logger

from toybox import Toybox, Input
from agents.base import *

from toybox.envs import get_turtle
from toybox.envs.atari.constants import ACTION_LOOKUP

from stable_baselines3.common.atari_wrappers import AtariWrapper
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3 import DQN, A2C, PPO

class StableBaselines(Agent, ABC):

    def __init__( self, toybox: Toybox, seed = 1234, action_repeat=4, frame_stack_size=1, *args, withstate = None,
      model_name = 'A2C', model_path = 'data/stablebaselines_a2c_amidar_1e4.regress.zip',
      additional_wrappers=lambda env: env,
      deterministic = False,
      ** kwargs):

      nenv = 1 # stable-baselines agents
      frame_stack_size = frame_stack_size
      env_type = 'atari'
      family = model_name

      # assert model exists
      self.model = self.getModel(family, seed, model_path)
      self.deterministic = False

      # The action_repeat value comes from the skip argument of
      self.action_repeat = action_repeat
      # MaxAndSkipEnv in atari_wrappers.py
      super().__init__(toybox, seed, action_repeat, *args, **kwargs)

      env_id = 'AmidarToyboxNoFrameskip-v4'
      # add a custom wrapper for Amidar resets
      env = self.setUpToyboxGym(self, env_id,
                                 seed=self.seed,
                                 frame_stack_size=frame_stack_size,
                                 additional_wrappers=additional_wrappers)

      self.env = env
      # self.model.set_env(env) if loading for retraining, need to set the model env
      obs = env.reset()
      self.obs = obs
      self.state = None

      self.turtle = get_turtle(self.env)
      self.turtle.toybox.set_seed(self.seed)
      self.toybox = toybox
      self._reset_seed(self.seed)
      if withstate: self.turtle.toybox.write_state_json(withstate)

      self.done = False
      self._frame_counter = 0
      self.lives = 1000
      self.cached_state = None

    @staticmethod
    def getModel(family, seed, model_path):
        family = family.lower()
        if family == "dqn":
            model = DQN.load(model_path)
        elif family == "a2c":
            model = A2C.load(model_path)
        elif family == "ppo":
            model = PPO.load(model_path)
        else:
            raise NameError(family) # no matching model family for this name string, break
        #model.seed(seed)
        return model

    @staticmethod
    def setUpToyboxGym(agentclass, env_id, seed, frame_stack_size=4, additional_wrappers = lambda env: env):
        env = gym.make(env_id, alpha=False,
                               grayscale=True)  # gym needs these tb constructor args with make_atari_env
        # allow a custom wrapper
        env = additional_wrappers(env)
        env = AtariWrapper(env, frame_skip=agentclass.action_repeat)
        if frame_stack_size > 1:
            env = VecFrameStack(env, n_stack=frame_stack_size)

        env.seed(seed)
        agentclass._reset_seed(seed)

        agentclass.env = env
        agentclass.turtle = get_turtle(env)
        agentclass.toybox = agentclass.turtle.toybox
        return env

    def wrap_predict(self, obs, state, deterministic):
      action, state = self.model.predict(obs, state=state, deterministic=deterministic)
      return action, state

    def get_action(self):
        inputobj = Input()
        action, state = self.wrap_predict(self.obs, self.state, self.deterministic)
        # modify input
        # convert returned action to input
        # Frameskip workaround if model maintains its own env
        # self.toybox.write_state_json(self.turtle.toybox.state_to_json())
        tb_action = self.toybox.get_legal_action_set()[action]
        ale_meaning = ACTION_MEANING[tb_action]
        inputobj = ALE_string_to_input(ale_meaning)
        if self.toybox.game_name == 'amidar' and inputobj:
            # don't allow fire
            inputobj.button1 = False
        done = self.done

        return inputobj if not done else None

    def resetEnv(self):
        self._frame_counter = 0
        self.lives = 1000
        self.done = False
        self.cached_state = None
        self.toybox.new_game()
        self.obs = self.env.reset()


    def stepEnv(self):
        action = self.get_action()
        obs, state, done, info = self.env.step(action)
        self._frame_counter += 1
        assert len(done) == 1 and len(
            info) == 1, 'Running with %d environments; should only be running with one.' % len(done)

        if 'cached_state' in info[0]:
            self.final_state = info[0]['cached_state']

        self.obs = obs
        self.done = done

if __name__ == '__main__':
  mzipname = "sb3_a2c_amidar_1e4.zip"

