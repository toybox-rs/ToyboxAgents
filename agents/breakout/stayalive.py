from base import Agent
import toybox.interventions.breakout as breakout

class StayAlive(Agent):

    def get_action(observation):
        return Input()


if __name__ == '__main__':
    with Toybox('breakout') as tb:
        agent = StayAlive(tb)
        agent.play('.')