#!/usr/bin/env python
# coding: utf-8

#get_ipython().run_line_magic('config', 'IPCompleter.greedy=True')
import pandas as pd
import numpy as np
from random import sample
from feature_prep import feature_construction
from sklearn.ensemble import RandomForestClassifier
import pickle
from collections import Counter


input_filename = '~/Documents/workspace/ToyboxAgents/analysis/data/data-from-emma/Target.csv'
outcome = 'aimed_left'
outcome_indicator = 'ball_hit'
# outcome = 'moved_left'
# outcome_indicator = float('nan')
num_pos_samples_per_episode = 10
num_neg_samples_per_episode = 10
time_lag = 6

construct_features = True
save_output = True
csv_filename = outcome+"-features.csv"

if construct_features:
    df = feature_construction(input_filename, outcome, outcome_indicator, save_output=save_output, output_filename=csv_filename)
else:
    df = pd.read_csv(csv_filename)


predictors = ['xpos_ball', 'xpos_pad', 'score', 'pad_width', 'ball_speed', 'ball_down',
              'l2_ball_pad', 'num_bricks_left', 'num_cols_0_bricks',
              'num_cols_1_brick', 'num_cols_2_bricks', 'bricks_right_of_paddle', 'bricks_left_of_paddle', 'channels_left_of_paddle',
              'channels_right_of_paddle', 'almost_channels_left_of_paddle', 'almost_channels_right_of_paddle']

# #### Discretize all predictors (outcome is already boolean)
# #### Convert booleans to 0,1

for predictor in predictors:
#    print(predictor)
    if isinstance(df[predictor][0], (np.bool_, bool)):
#        print(predictor + " is boolean")
        # convert booleans to 0/1 rather than 'True'/'False'
        df[predictor] = [1 if val == 'True' else 0 for val in df[predictor]]
    if isinstance(df[predictor][0], str):
        if len(np.unique(df[predictor])) > 2:
            print("warning: " + predictor + " should be converted into numbers")
        else:  # don't discretize, just convert to integer values, since order is irrelevant if there are only two possible values
            df[predictor] = [1 if val == df[predictor][0] else 0 for val in df[predictor]]

# #### For each seed, get all positive data points and sample an equal number of negative data points
#
# num_pos_samples_per_episode is how many positive samples ot take from every episode
# num_neg_samples_per_episode is how many negative samples to take from every episode
#
# the time points sampled represent the covariates time point - we'll have to get the outcome frome time_lag steps later
#
# Make sure the sampled time points aren't within time_lag of the beginning of an episode (so we can sample the covariates from before that)


samples = []
for seed in np.unique(df['seed']):
    df_seed = df[df.seed == seed]
    positive_samples_t = df_seed[df_seed.outcome & (df_seed.t >= time_lag)].t.values - time_lag
    positive_samples_t = sample(list(positive_samples_t), min(num_pos_samples_per_episode, len(positive_samples_t)))
    positive_samples = df_seed[[t in positive_samples_t for t in df_seed.t]]
    positive_samples = positive_samples.assign(outcome=True)

    negative_samples_t = df_seed[
                             ~df_seed.outcome & df_seed.outcome_indicator & (df_seed.t >= time_lag)].t.values - time_lag
    negative_samples_t = sample(list(negative_samples_t), min(num_neg_samples_per_episode, len(negative_samples_t)))
    negative_samples = df_seed[[t in negative_samples_t for t in df_seed.t]]
    negative_samples = negative_samples.assign(outcome=False)

    samples.append(positive_samples)
    samples.append(negative_samples)
samples = pd.concat(samples)

print(samples.shape)

# ### Learn model of outcome given covariates

rf = RandomForestClassifier(n_estimators=1000)

rf.fit(samples[predictors], samples['outcome'])

# ### In order to answer counterfactual queries, we're going to need to discretize each predictor
# ### For consistency, then, we'll discretize now, and use those discretized bins for the joint model
#
# This code doesn't actually apply the discretization scheme to any of the data.  It just calculates the discretization intervals and saves them in discretization_dict

num_discretization_bins = 5

discretization_dict = dict()
for predictor in predictors:
    if isinstance(df[predictor][0], float) | len(pd.unique(df[predictor])) > 8:
#        print("Discretizing " + predictor)
        not_discretized_yet = True
        curr_num_bins = 1

        while not_discretized_yet:
            try:
                if curr_num_bins == 1:  # we can't do a single bin, so give up on density-based binning
#                    print("Giving up on discretizing " + predictor + " using density-based binning")
                    discretization = list(pd.cut(df[predictor], bins=num_discretization_bins))
                else:
                    discretization = list(pd.qcut(df[predictor], q=curr_num_bins))
                discretization_dict[predictor] = sorted(np.unique(discretization))  # save the discretization scheme

                # set the endpoints to -inf and inf
                #            for i in range(0, len(discretization)):
                #                if discretization[i] == discretization_dict[predictor][0]:#set lower endpoint to 0
                #                    discretization[i] = pd.Interval(-float("inf"), discretization[i].right)
                #                if discretization[i] == discretization_dict[covar][len(discretization_dict[predictor])-1]:
                #                    discretization[i] = pd.Interval(discretization[i].left, float("inf"))

                discretization_dict[predictor] = sorted(np.unique(discretization))
#                print(discretization_dict[predictor])

                not_discretized_yet = False
#                print("Discretizing " + predictor + " into " + str(len(np.unique(discretization))) + " bins\n")

            except ValueError:
                curr_num_bins -= 1

# ### Learn joint model of covariates, in the form of separate predictive random forests for each covariate
rf_dict = dict()
for covar in predictors:
    print(covar)
    if covar in discretization_dict.keys():  # need to apply discretization scheme to the current covar
        discretization = discretization_dict[covar]
        val_to_discretize = samples[covar]
        val_discretized = []
        for val in val_to_discretize:
            is_disc_value = [val in disc for disc in
                             discretization]  # figure out which discretization category the value is in
            val_discretized.append(
                discretization[np.where(is_disc_value)[0][0]])  # get the actual interval corresponding to that location
        curr_outcome = [str(val) for val in val_discretized]
    else:
        curr_outcome = samples[covar]
    rf_dict[covar] = RandomForestClassifier(n_estimators=100)
    rf_dict[covar].fit(samples[predictors].loc[:, samples[predictors].columns != covar], curr_outcome)

# ### Now that we've learned all the relevant models, we can finally provide counterfactual explanations!
# - take in a query time point (must satisfy outcome_indicator)
# - apply the time lag
# - iterate over all possible (discretized) values for all predictors
# - for each value, check if the predicted outcome crosses over the .5 threshold to give a different prediction
# - if so, this is an explanation - report the likelihood of this explanation using the corresponding covariate model#



query = df.loc[sample(list(df[df.outcome_indicator].index), 1)]
print(query)
# query = df.loc[[32720]]
query_tick = list(query.t)[0]
query_seed = list(query.seed)[0]
observed_outcome = list(query.outcome)[0]

if query_tick - time_lag < 0:
    print("ERROR - invalid query time (too early in episode)")

# apply the time lag
query = df[(df.t == (query_tick - time_lag)) & (df.seed == query_seed)]
query.outcome = observed_outcome

possible_explanations = pd.DataFrame(columns=['variable', 'from_value', 'to_value', 'relative_prob'])
pred_outcome = rf.predict(query[predictors])[0]
if pred_outcome != observed_outcome:
    print("Unexpected outcome - model prediction differs from observation")

for var in predictors:
    observed_val = query[var].iloc[0]
    #    print("observed: " + str(observed_val))
    if var in discretization_dict.keys():
        #        print(var + " was discretized!")
        possible_ranges = discretization_dict[var].copy()
        observed_val = possible_ranges[np.where([(observed_val in curr_range) for curr_range in possible_ranges])[0][0]]
        possible_ranges.remove(observed_val)
        # sample from the ranges to get actual values for intervention
        possible_vals = [np.random.uniform(curr_range.left, curr_range.right) for curr_range in possible_ranges]
    else:
        #        print(var + " was not discretized!")
        possible_vals = list(np.unique(df[var]))
        possible_vals.remove(observed_val)

    # loop over the possible different values for var, and see if they change the predicted outcome
    vals_with_different_outcome = []
    for val in possible_vals:
        intervened_covars = query.copy(deep=True)
        intervened_covars[var] = val
        intervened_outcome = rf.predict(intervened_covars[predictors])
        intervened_prob = rf.predict_proba(intervened_covars[predictors])
        outcome_probs = rf.predict_proba(intervened_covars[predictors])

        if intervened_outcome != observed_outcome:
            vals_with_different_outcome.append(val)
        print(intervened_prob)


    if len(vals_with_different_outcome) == 0:
        print("No interventions found for " + str(var))
    else:
        print("These settings of " + str(var) + " change the outcome: " + str(vals_with_different_outcome))

    # Now apply the covariate model to get the relative probabilities of these new values for var
    covar_rf = rf_dict[var]
    covar_classes = [str(curr_class) for curr_class in list(covar_rf.classes_)]
    for val in vals_with_different_outcome:
        if var in discretization_dict.keys():
            val = possible_ranges[np.where([(val in curr_range) for curr_range in possible_ranges])[0][0]]
        model_preds = covar_rf.predict_proba(query[predictors].loc[:, query[predictors].columns != var])[0]
        #        print(model_preds)
        #        print("observed_val = " + str(observed_val))
        #        print("intervened_val = " + str(val))
        observed_prob = model_preds[covar_classes.index(str(observed_val))]
        if ~(val in covar_classes):
            intervened_prob = 0
        else:
            intervened_prob = model_preds[covar_classes.index(str(val))]
        print(model_preds)
        print(str(intervened_prob) + "/" + str(observed_prob))

        if observed_prob == 0:
            change_prob = 0
        else:
            change_prob = intervened_prob / observed_prob
        possible_explanations.loc[len(possible_explanations)] = [var, observed_val, val, change_prob]

print(possible_explanations)

