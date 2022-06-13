############################################################################################
''' model that gets posterior estimates of task set and other parameters for the "quantum task"
Originally in matalb by JF, converted to python by Steph. 
Kai commented questions
'''
################
# set up packages
import numpy as np
import numpy.matlib as mb
import matplotlib.pyplot as plt
import scipy as sp
from scipy import stats
import seaborn as sns
import os
import pickle
plt.ion()
# initialize data directory and other useful variables
data_dir = os.getcwd()
os.chdir(data_dir)
print(data_dir)


###################################################
### simulate a sequence
###################################################
#function [tState, tProp, tResp, tTask] = SequenceSimulation(nTrials, switchRange, thetas)
def SequenceSimulation(nTrials, switchRange, thetas):

  #rng; # NEED TO FIND PYTHON EQUIVALENT

  tState = np.array([])
  cState = 0
  l = 0
  r = np.array(range(switchRange[0],(switchRange[1]+1),1)) 

  # set up state based on switch range
  while l < nTrials:
    #r = r[np.random.permutation(len(r))]
    #tState = np.concatenate( (tState, mb.repmat(cState, 1, r[0]).flatten()), axis=None )
    r = np.random.choice([15,25])
    tState = np.concatenate( (tState, mb.repmat(cState, 1, r).flatten()), axis=None )
    cState = 1 - cState
    l = l + r
    #l = l + r[0]

  tState = tState[:nTrials] # make sure tState is only as long as the number of trials
  
  tProp = np.random.rand(nTrials) # randomly generate proportion (cue)... btw 0 and 1
  possible_prop = [0.11111111,0.33333333,0.44444444,0.48,0.52,0.55555556,0.66666667,0.88888889]
  # avoid extreme values in simulation
  tProp[tProp < 0.05] = 0.05
  tProp[tProp > 0.95] = 0.95

  tResp = np.zeros((tState.shape))
  tTask = np.zeros((tState.shape))

  # loop through all trials
  for i in range(nTrials):
    np.random.shuffle(possible_prop)
    tProp[i] = possible_prop[0]

    x = np.exp(thetas[0]) * np.log( (tProp[i]/(1 - tProp[i])) )
    p = 1 / (1 + np.exp((-1*x)))

    # agent got confused within 3 trials after switch
    if (i > 4) and ( (tState[i] != tState[(i-1)]) or (tState[i] != tState[(i-2)]) or (tState[i] != tState[(i-3)])):
      # if we are within 3 trials of a switch then assume they're still doing the old task
      cState = 1 - tState[i]
    else:
      # if we are within the first 3 task trials assume they are randomly guessing
      if i < 4:
        if np.random.rand() < 0.5:
          cState = 0
        else:
          cState = 1
      else:
        cState = tState[i]

    if ( (tProp[i] > 0.5) and (tState[i] == 0) ) or ( (tProp[i] < 0.5) and (tState[i] > 0) ):
      tTask[i] = 0
    else:
      tTask[i] = 1

    # rTask is the simulated task the agent thinks it should do
    if np.random.rand() < p:
      #color 0
      if cState == 0:
        rTask = 0
      else:
        rTask = 1
    else:
      #color 1
      if cState == 0:
        rTask = 1
      else:
        rTask = 0

    if tTask[i] != rTask:
      tResp[i] = 2
    else:
      if rTask == 0:
        if np.random.rand() < thetas[1]:
          tResp[i] = 1
        else:
          tResp[i] = 0
      else:
        if np.random.rand() < thetas[2]:
          tResp[i] = 1
        else:
          tResp[i] = 0

  return tState, tProp, tResp, tTask

thetas = [np.log(1.2), 0.09, 0.07]  #logistic regression slope, error rate for two tasks
tState, tProp, tResp, tTask = SequenceSimulation(300, [15, 25], thetas)


#####################################################################################
"""maximum posterior estimator of joint distribution of state and
hyperparameters

input:
tState: trial wise task-set (0: color 0 = face, color 1 = scene; 1: color 0 = scene, color 1 = face)
tProp: trial-wise proportion of dots (0 - 1, for the first color)
tResp: trial-wise response: 0 = correct, 1 = correct task wrong answer, 2 = wrong task

output:
jd: joint distribution of parameters at the end of experiment
sE: trial-wise estimate of state, encoding probability of state 0
tE: trial-wise estimate of task, encoding probability of task 0
mDist: marginal distribution for the 4 thetas,
rRange: values of the thetas

notes on parameters:
Theta 0: probability of task state 0 and state 1
Theta 1: logistic function slope parameter converting sensory input to color perception
Theta 2: face task error rate
Theta 3: scene task error rate
Theta 4: diffusion of task set across trials

###############????????????????????????????????????????????????????######
Question 1, for the hyperparameters theta, looks like theta0 has two dimensions, which the prob distributions of task state 0 and 1?
For theta4, What is the purpose of task set diffusion?
###############????????????????????????????????????????????????????######

###############????????????????????????????????????????????????????######
Question 2: is my understanding of the bayes update of the model below correct?
p(thetas | response, color_ratio) = liklihood * p(prior thetas)
not sure how liklihood is paramterized here, just p(Response) and p(Color_ratio)?  
Ask JF of how the lilihood update is calcuated in the model
###############????????????????????????????????????????????????????######
"""


#function [jd, sE, tE, mDist, pRange] = MPEModel(tState, tProp, tResp)
def MPEModel(tState, tProp, tResp):
    
    sE = []
    tE = []

    #start with uniform prior
    #pRange = cell(1, 4);
    pRange = {'lfsp':np.linspace(-5, 5, 201, endpoint=True), 'fter':np.linspace(0, 0.5, 51, endpoint=True), 'ster':np.linspace(0, 0.5, 51, endpoint=True), 'diff_at':np.linspace(0, 0.5, 51, endpoint=True)}
    #range of logistic function slope parameter
    #pRange{1} = -5:0.05:5;
    #range of face task error rate
    #pRange{2} = 0:0.01:0.2;
    #range of scene task error rate
    #pRange{3} = 0:0.01:0.2;
    #diffusion across trials
    #pRange{4} = 0:0.01:0.5;
    #dim = [2, length(pRange{1}), length(pRange{2}), length(pRange{3}), length(pRange{4})];
    dim = np.array( [2, len(pRange['lfsp']), len(pRange['fter']), len(pRange['ster']), len(pRange['diff_at'])] )
    
    total = 1
    # for i = 1:length(dim)
    # total = total * dim(i);
    # end
    # jd = ones(dim) / total;
    for c_dim in dim:
        total = total * c_dim
    jd = np.ones(dim) / total   # the division of total is to normalize values into probability
     

    #likelihood of getting correct response
    #ll = zeros(size(jd));
    ll = np.zeros(jd.shape)

    #tProp = log(tProp ./ (1 - tProp));

    ###############????????????????????????????????????????????????????######
    # Question 3, here why taking the log of ratio of dots for the two colors?
    # Make it more normal?
    ###############????????????????????????????????????????????????????######
    tProp = np.log(tProp / (1 - tProp))  

    # for i = 1 : length(tState)
    # if mod(i, 20) == 0
    #     disp([num2str(i) ' trials have been simulated.']);
    # end
    for it in range(len(tState)):
        if (it % 50) == 0:
            print(str(it), ' trials have been simulated.')
        #diffusion of joint distribution over trials
        # for i4 = 1 : dim(4)
        #     x = (jd(1, :, :, :, i4) + jd(2, :, :, :, i4)) / 2;

        #     jd(1, :, :, :, i4) = jd(1, :, :, :, i4) * (1 - pRange{4}(i4)) + pRange{4}(i4) * x;
        #     jd(2, :, :, :, i4) = jd(2, :, :, :, i4) * (1 - pRange{4}(i4)) + pRange{4}(i4) * x;
        # end

        ###############????????????????????????????????????????????????????######    
        ###############????????????????????????????????????????????????????######
        # Question 4, what is the purpose of this block of code below? 
        # it appears the effect is essentially to smooth paramters between task state 0 and 1??
        
        for i4 in range(dim[4]):
            x = (jd[0, :, :, :, i4] + jd[1, :, :, :, i4]) / 2

            jd[0, :, :, :, i4] = jd[0, :, :, :, i4] * (1 - pRange['diff_at'][i4]) + pRange['diff_at'][i4] * x
            jd[1, :, :, :, i4] = jd[1, :, :, :, i4] * (1 - pRange['diff_at'][i4]) + pRange['diff_at'][i4] * x
        #add estimate as marginalized distribution
        #sE(end + 1) = sum(sum(sum(sum(jd(1, :, :, :, :)))));
        sE.append(np.sum(jd[0, :, :, :, :]))
        ###############????????????????????????????????????????????????????######
        ###############????????????????????????????????????????????????????######


        #first color logit greater than 0 means it is dominant, less than 0
        #means other color dominant

        ############################################
        #### below is the mapping between color ratio, task state, and task
        # tState = 0, tProp<0 : tTask = 1
        # tState = 0, tProp>0 : tTask = 0 
        # tState = 1, tProp<0 : tTask = 0
        # tState = 1, tProp<0 : tTask = 1
        if ((tProp[it] < 0) and (tState[it] > 0)) or ((tProp[it] > 0) and (tState[it] == 0)):
            tTask = 0
        else:
            tTask = 1
        ################################################


        # S_Theta1 = squeeze(sum(sum(sum(jd, 3), 4), 5));
        # tE(end + 1) = 0;
        # here marginalize theta1
        S_Theta1 = np.squeeze(np.sum(np.sum(np.sum(jd, 4), 3), 2)) # double check that axes are correct
        
        tE.append(0)
        for i0 in range(dim[0]):
            for i1 in range(dim[1]):

                ###############????????????????????????????????????????????????????######
                ###############????????????????????????????????????????????????????######
                # Question 5:
                # here this block to logit transform  color ratio to probability of color decision.
                # I believe the formula from JF's white borad was:
                # p(pColor | tProp) = 1 / (1 + exp( -1* theta1 * log(tProp) ))
                #  
                # and convert the color decision probability to task belief (0 to 1)
                # The last line task multiply with S_Theta1 (the marginalized set belief and logistic function slope),
                # is it to weight the task belief by the probability of each logistic slope param in the distribution for each task set...?

                                                     # Quesion 6 here   
                theta1 = np.exp(pRange['lfsp'][i1])  # why take the exponent of logisitc function slope??
                pColor = 1 / (1 + np.exp((-1*theta1) * tProp[it]))
                if i0 == 0:
                    pTask0 = pColor
                else:
                    pTask0 = 1 - pColor

                #print(tE[-1] + pTask0 * S_Theta1[i0, i1])
                tE[-1] = tE[-1] + pTask0 * S_Theta1[i0, i1] 
                ###############????????????????????????????????????????????????????######
                ###############????????????????????????????????????????????????????######


                for i2 in range(dim[2]):
                    for i3 in range(dim[3]):
                        #pP is the likelihood, change this if there is only one type of error
                        # this is for separated response error and task error
                        
                        ###############????????????????????????????????????????????????????######
                        ###############????????????????????????????????????????????????????######
                        # question 7
                        # dont quite get what the liklihood here means given the three typoes of response below
                        # trial-wise response: 0 = correct, 1 = correct task wrong answer, 2 = wrong task
                        if tTask == 0:
                            pP = [pTask0 * (1 - pRange['fter'][i2]), pTask0 * pRange['fter'][i2], (1 - pTask0)]
                        else:
                            pP = [(1 - pTask0) * (1 - pRange['ster'][i3]), (1 - pTask0) * pRange['ster'][i3], pTask0]
                            print(pP)
                        
                        #posterior, jd now is prior
                        ######
                        # question 8
                        # Here it appears you are using one of the three liklihood to update all joint thetas, will have to ask
                        # JF the logic of othis operation
                        ll[i0, i1, i2, i3, :] = jd[i0, i1, i2, i3, :] * pP[int(tResp[it])]
                        ###############????????????????????????????????????????????????????######
                        ###############????????????????????????????????????????????????????######

                        # #this is for only one type of error
                        # if tTask == 0:
                        #     pP = [pTask0 * (1 - pRange['fter'][i2]), pTask0 * pRange['fter'][i2] + (1 - pTask0)]
                        # else:
                        #     pP = [(1 - pTask0) * (1 - pRange['ster'][i3]), (1 - pTask0) * pRange['ster'][i3] + pTask0]
                        
                        # #posterior, jd now is prior
                        # if tResp(i) == 0:
                        #     ll[i0, i1, i2, i3, :] = jd[i0, i1, i2, i3, :] * pP[0]
                        # else:
                        #     ll[i0, i1, i2, i3, :] = jd[i0, i1, i2, i3, :] * pP[1]
                        
        #normalize
        jd = ll / np.sum(ll)
    
        mDist={}
        mDist['lfsp'] = np.squeeze(np.sum(np.sum(np.sum(np.sum(jd, 4), 3), 2), 0))    # 4 3 2 0
        mDist['fter'] = np.squeeze(np.sum(np.sum(np.sum(np.sum(jd, 4), 3), 1), 0))    # 4 3 1 0
        mDist['ster'] = np.squeeze(np.sum(np.sum(np.sum(np.sum(jd, 4), 2), 1), 0))    # 4 2 1 0
        mDist['diff_at'] = np.squeeze(np.sum(np.sum(np.sum(np.sum(jd, 3), 2), 1), 0)) # 3 2 1 0
    
    return jd, sE, tE, mDist, pRange





"""
CONTROL MODEL
maximum posterior estimator of joint distribution of state and hyperparameters
both color perception and task-set beliefs might become deterministic before deciding what task to perform. 
Therefore, the control model holds that task-set beliefs might become deterministic.

input:
tState: trial wise task-set (0: color 0 = face, color 1 = scene; 1: color 0 = scene, color 1 = face)
tProp: trial-wise proportion of dots (0 - 1, for the first color)
tResp: trial-wise response: 0 = correct, 1 = correct task wrong answer, 2 = wrong task

output:
jd: joint distribution of parameters at the end of experiment
sE: trial-wise estimate of state, encoding probability of state 0
tE: trial-wise estimate of task, encoding probability of task 0
mDist: marginal distribution for the 4 thetas,
rRange: values of the thetas"""

#function [jd, sE, tE, mDist, pRange] = MPEModel(tState, tProp, tResp)
def MPEModel_Control(tState, tProp, tResp):
    
    sE = []
    tE = []

    #start with uniform prior
    #pRange = cell(1, 4);
    pRange = {'lfsp':np.linspace(-5, 5, 201, endpoint=True), 'fter':np.linspace(0, 0.5, 21, endpoint=True), 'ster':np.linspace(0, 0.5, 21, endpoint=True), 'diff_at':np.linspace(0, 0.5, 21, endpoint=True)}
    #pRange = {'lfsp':np.linspace(-5, 5, 201, endpoint=True), 'fter':np.linspace(0, 0.5, 51, endpoint=True), 
    #          'ster':np.linspace(0, 0.5, 51, endpoint=True), 'diff_at':np.linspace(0, 0.5, 51, endpoint=True)}
    
    #range of logistic function slope parameter
    #pRange{1} = -5:0.05:5;
    #range of face task error rate
    #pRange{2} = 0:0.01:0.2;
    #range of scene task error rate
    #pRange{3} = 0:0.01:0.2;
    #diffusion across trials
    #pRange{4} = 0:0.01:0.5;
    #dim = [2, length(pRange{1}), length(pRange{2}), length(pRange{3}), length(pRange{4})];
    dim = np.array( [2, len(pRange['lfsp']), len(pRange['fter']), len(pRange['ster']), len(pRange['diff_at'])] )

    total = 1
    # for i = 1:length(dim)
    # total = total * dim(i);
    # end
    # jd = ones(dim) / total;
    for c_dim in dim:
        total = total * c_dim
    jd = np.ones(dim) / total
    
    #likelihood of getting correct response
    #ll = zeros(size(jd));
    ll = np.zeros(jd.shape)

    #tProp = log(tProp ./ (1 - tProp));
    tProp = np.log(tProp / (1 - tProp))

    # for i = 1 : length(tState)
    # if mod(i, 20) == 0
    #     disp([num2str(i) ' trials have been simulated.']);
    # end
    for it in range(len(tState)):
        if (it % 50) == 0:
            print(str(it), ' trials have been simulated.')
        #diffusion of joint distribution over trials
        # for i4 = 1 : dim(4)
        #     x = (jd(1, :, :, :, i4) + jd(2, :, :, :, i4)) / 2;

        #     jd(1, :, :, :, i4) = jd(1, :, :, :, i4) * (1 - pRange{4}(i4)) + pRange{4}(i4) * x;
        #     jd(2, :, :, :, i4) = jd(2, :, :, :, i4) * (1 - pRange{4}(i4)) + pRange{4}(i4) * x;
        # end
        for i4 in range(dim[4]):
            x = (jd[0, :, :, :, i4] + jd[1, :, :, :, i4]) / 2

            jd[0, :, :, :, i4] = jd[0, :, :, :, i4] * (1 - pRange['diff_at'][i4]) + pRange['diff_at'][i4] * x
            jd[1, :, :, :, i4] = jd[1, :, :, :, i4] * (1 - pRange['diff_at'][i4]) + pRange['diff_at'][i4] * x
        #add estimate as marginalized distribution
        #sE(end + 1) = sum(sum(sum(sum(jd(1, :, :, :, :)))));
        sE.append(np.sum(jd[0, :, :, :, :]))

        #first color logit greater than 0 means it is dominant, less than 0
        #means other color dominant
        if ((tProp[it] < 0) and (tState[it] > 0)) or ((tProp[it] > 0) and (tState[it] == 0)):
            tTask = 0
        else:
            tTask = 1

        # S_Theta1 = squeeze(sum(sum(sum(jd, 3), 4), 5));
        # tE(end + 1) = 0;
        S_Theta1 = np.squeeze(np.sum(np.sum(np.sum(jd, 4), 3), 2)) # double check that axes are correct
        
        # Making task-set decisions deterministic
        ###############????????????????????????????????????????????????????######
        ###############????????????????????????????????????????????????????######
        # ask JF how this part works to make it determinsitic
        for i0 in range(S_Theta1.shape[1]):
            if S_Theta1[0, i0] > S_Theta1[1, i0]:
                S_Theta1[0, i0] += S_Theta1[1, i0]
                S_Theta1[1, i0] = 0
            else:
                S_Theta1[0, i0] = 0
                S_Theta1[1, i0] += S_Theta1[0, i0]
        ###############????????????????????????????????????????????????????######
        ###############????????????????????????????????????????????????????######
        
        tE.append(0)
        for i0 in range(dim[0]):
            for i1 in range(dim[1]):
                theta1 = np.exp(pRange['lfsp'][i1])
                pColor = 1 / (1 + np.exp((-1*theta1) * tProp[it]))
                
                # Making color perception deterministic
                if pColor > 0.5:
                    pColor = 1
                else:
                    pColor = 0
                
            
                if i0 == 0:
                    pTask0 = pColor
                else:
                    pTask0 = 1 - pColor

                #print(tE[-1] + pTask0 * S_Theta1[i0, i1])
                #print(tE[-1])
                #print(pTask0 * S_Theta1[i0, i1])
                tE[-1] = tE[-1] + pTask0 * S_Theta1[i0, i1] 
                for i2 in range(dim[2]):
                    for i3 in range(dim[3]):
                        #pP is the likelihood, change this if there is only one type of error
                        # this is for separated response error and task error
                        if tTask == 0:
                            pP = [pTask0 * (1 - pRange['fter'][i2]), pTask0 * pRange['fter'][i2], (1 - pTask0)]
                        else:
                            pP = [(1 - pTask0) * (1 - pRange['ster'][i3]), (1 - pTask0) * pRange['ster'][i3], pTask0]
                        
                        #posterior, jd now is prior
                        ll[i0, i1, i2, i3, :] = jd[i0, i1, i2, i3, :] * pP[int(tResp[it])]

                        # #this is for only one type of error
                        # if tTask == 0:
                        #     pP = [pTask0 * (1 - pRange['fter'][i2]), pTask0 * pRange['fter'][i2] + (1 - pTask0)]
                        # else:
                        #     pP = [(1 - pTask0) * (1 - pRange['ster'][i3]), (1 - pTask0) * pRange['ster'][i3] + pTask0]
                        
                        # #posterior, jd now is prior
                        # if tResp(i) == 0:
                        #     ll[i0, i1, i2, i3, :] = jd[i0, i1, i2, i3, :] * pP[0]
                        # else:
                        #     ll[i0, i1, i2, i3, :] = jd[i0, i1, i2, i3, :] * pP[1]
                        
        #normalize
        jd = ll / np.sum(ll)
    
        mDist={}
        mDist['lfsp'] = np.squeeze(np.sum(np.sum(np.sum(np.sum(jd, 4), 3), 2), 0))    # 4 3 2 0
        mDist['fter'] = np.squeeze(np.sum(np.sum(np.sum(np.sum(jd, 4), 3), 1), 0))    # 4 3 1 0
        mDist['ster'] = np.squeeze(np.sum(np.sum(np.sum(np.sum(jd, 4), 2), 1), 0))    # 4 2 1 0
        mDist['diff_at'] = np.squeeze(np.sum(np.sum(np.sum(np.sum(jd, 3), 2), 1), 0)) # 3 2 1 0
    
    return jd, sE, tE, mDist, pRange
  