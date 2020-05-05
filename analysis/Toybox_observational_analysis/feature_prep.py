import pandas as pd
import numpy as np


def feature_construction(input_filename, outcome, outcome_indicator, save_output=True, output_filename = "./output.csv"):
    df = pd.read_csv(input_filename)

    # Convert the 'board_alive' variable to brick counts by column
    new_col_data = []
    new_col_names = ["bricks_in_col_" + str(col).zfill(2) for col in range(0, 18)]

    for col in new_col_names:  # add new (empty) columns to the dataframe
        df[col] = -1

    for row in range(0, len(df.index)):
        board_alive = bin(int(df['board_alive'][row]))[2:].zfill(108)
        cols = [board_alive[(i * 6):(i * 6 + 6)] for i in
                range(0, 18)]  # pull out each column from the binary string (every 7 digits)
        col_counts = [sum([int(val) for val in list(col)]) for col in
                      cols]  # convert each string to a list of ints and sum them
        new_col_data.append(col_counts)

    df[new_col_names] = new_col_data

    # Correct 'ball_down' to correctly be False when the ball is maintaining its height
    dfs = []
    for seed in np.unique(df.seed):
        df_seed = df[df.seed == seed].copy(deep=True)
        df_seed['ypos_ball_next'] = [
            list(df_seed.loc[df_seed['t'] == t + 1, 'ypos_ball'])[0] if (t + 1) in df_seed['t'].values else float('nan') for
            t in df_seed.t]

        df_seed['ball_down'] = [
            False if list(df_seed[df_seed.t == t].ypos_ball == df_seed[df_seed.t == t].ypos_ball_next)[0] else
            list(df_seed[df_seed.t == t].ball_down)[0] for t in df_seed.t]
        dfs.append(df_seed)

    df = pd.concat(dfs)


    # ### Create variables from the column counts
    df['num_cols_0_bricks'] = [sum(df.iloc[row][new_col_names] == 0) for row in range(0, len(df.index))]
    df['num_cols_1_brick'] = [sum(df.iloc[row][new_col_names] == 1) for row in range(0, len(df.index))]
    df['num_cols_2_bricks'] = [sum(df.iloc[row][new_col_names] == 2) for row in range(0, len(df.index))]


    # hard-coded column positions, taken from the json of a random Breakout game
    col_positions = [i * 12 for i in range(1, 19)]

    #Create variables about channels/bricks relative to paddle position
    bricks_left_of_paddle = []
    bricks_right_of_paddle = []
    channels_left_of_paddle = []
    channels_right_of_paddle = []
    almost_channels_left_of_paddle = []
    almost_channels_right_of_paddle = []

    for row in range(0, len(df.index)):
        paddle_pos = df.iloc[row]['xpos_pad']
        cols_left_of_paddle = np.where(col_positions < paddle_pos)[0]  # get which columns are left of paddle
        cols_left_of_paddle = [str(i).zfill(2) for i in
                               cols_left_of_paddle]  # convert into a padded string to match column names
        cols_right_of_paddle = np.where(col_positions > paddle_pos)[0]  # get which columns are left of paddle
        cols_right_of_paddle = [str(i).zfill(2) for i in
                                cols_right_of_paddle]  # convert into a padded string to match column names

        prefix = new_col_names[0][0:(len(new_col_names[0]) - 2)]
        cols_left_of_paddle = [prefix + col for col in cols_left_of_paddle]  # add the prefix to match column names
        cols_right_of_paddle = [prefix + col for col in cols_right_of_paddle]  # add the prefix to match column names

        vals_left_of_paddle = df.iloc[row][cols_left_of_paddle]
        vals_right_of_paddle = df.iloc[row][cols_right_of_paddle]
        bricks_left_of_paddle.append(sum(vals_left_of_paddle))
        bricks_right_of_paddle.append(sum(vals_right_of_paddle))

        channels_left_of_paddle.append(sum(vals_left_of_paddle == 0))
        channels_right_of_paddle.append(sum(vals_right_of_paddle == 0))

        almost_channels_left_of_paddle.append(sum([(val in [1, 2]) for val in vals_left_of_paddle]))
        almost_channels_right_of_paddle.append(sum([(val in [1, 2]) for val in vals_right_of_paddle]))

    df['bricks_left_of_paddle'] = bricks_left_of_paddle
    df['bricks_right_of_paddle'] = bricks_right_of_paddle
    df['channels_left_of_paddle'] = channels_left_of_paddle
    df['channels_right_of_paddle'] = channels_right_of_paddle
    df['almost_channels_left_of_paddle'] = almost_channels_left_of_paddle
    df['almost_channels_right_of_paddle'] = almost_channels_right_of_paddle


    #We have to do some data cleaning - some predictors have NaN fields
    # - remove any rows that have no action
    # - for xpos_ball_prev and ypos_ball_prev at t=0, set to xpos_ball and ypos_ball
    # - same for xpos_pad_prev and ypos_pad_prev
    has_action = [not pd.isnull(val) for val in df['action']]
    df = df[has_action]

    nans = np.isnan(df['xpos_ball_prev'])
    df.loc[nans, 'xpos_ball_prev'] = df.loc[nans, 'xpos_ball']
    df.loc[nans, 'ypos_ball_prev'] = df.loc[nans, 'ypos_ball']

    nans = np.isnan(df['xpos_pad_prev'])
    df.loc[nans, 'xpos_pad_prev'] = df.loc[nans, 'xpos_pad']
    df.loc[nans, 'ypos_pad_prev'] = df.loc[nans, 'ypos_pad']

    #### Define outcome variable, current options are:
    # - Why did you move left?
    # - Why did you aim left?
    #   - only defined at the point when the paddle hits the ball (use dummy value otherwise)
    #   - locate every time step where the ball hits the paddle
    #   - compare the relative position of the ball at its 'hit' time step to its position at the following time step
    #     - (if following time step, ball's x position < current x position, outcome = TRUE, otherwise outcome = FALSE)
    #

    # why did you move left?
    if outcome == 'move_left':
        df['outcome'] = (df['action'] == 'left')

    # why did you aim left?
    if outcome == 'aimed_left':
        dfs = []
        # break it down by seed, to make sure we can look at the next time step easily
        for seed in np.unique(df['seed']):
            df_seed = df[df['seed'] == seed].copy(deep=True)
            df_seed['ball_down_prev'] = [
                list(df_seed.loc[df_seed['t'] == t - 1, 'ball_down'])[0] if (t - 1) in df_seed['t'].values else float('nan')
                for t in df_seed['t']]
            df_seed['ball_hit'] = [
                (df_seed.loc[row, 'ball_down_prev'] == True) & (df_seed.loc[row, 'ball_down'] == False) & (
                            df_seed.loc[row, 'ypos_ball'] > 130) for row in df_seed.index]

            df_seed['aimed_left'] = [((list(df_seed[df_seed.t == t]['xpos_ball'])[0] >
                                       list(df_seed[df_seed.t == t + 2]['xpos_ball'])[0]) &
                                      list(df_seed[df_seed.t == t]['ball_hit'])[0]) if (t + 2) in df_seed.t.values else False
                                     for t in df_seed.t]
            df_seed['aimed_right'] = [((list(df_seed[df_seed.t == t]['xpos_ball'])[0] <
                                        list(df_seed[df_seed.t == t + 2]['xpos_ball'])[0]) &
                                       list(df_seed[df_seed.t == t]['ball_hit'])[0]) if (t + 2) in df_seed.t.values else False
                                      for t in df_seed.t]

            dfs.append(df_seed)

        df = pd.concat(dfs)

        df['outcome'] = df['aimed_left']

    #check outcome indicator and set it appropriately (should be NaN if any time point is valid for outcome)
    if pd.isnull(outcome_indicator):
        df['outcome_indicator'] = True
    else:
        df['outcome_indicator'] = df[outcome_indicator]

    if save_output:
        df.to_csv(output_filename, index=False)

    return(df)