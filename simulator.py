# Implements a real-time system simulator based on a simplified model, widely used in industry.
#
# The simulator compares scheduling performance between a random scheduler
# and Earliest Deadline First scheduling when clock speed is variable.
#
# Results are saved to a local .csv file. To compare how many task sets one algorithm 'won', find the column titled EDFwins or RandWins.
# Past example results can be found in the 'Results' subdirectory for different simulator configurations.
#
# Python version used: 2.7.6
# For best performance when using large task sets, use the pypy implementation of Python.
#
# Richard Lindsay, 2018

import time, random, math, csv, uuf

class Task:
    """Task object defining various properties of a task in the system"""

    def __init__(self, period, deadline, compTime):
        self.C = compTime
        self.T = period
        self.D = deadline
        self.U = compTime/period
        self.lastRelease = 0
        self.nextRelease = 0
        self.nextD = deadline
        self.runTime = 0
        self.released = False
        self.isRunning = False
        self.missTime = 0
        self.worstMiss = 0
        self.partialMiss = 0
        self.lastMiss = False
        self.lastMissTime = 0
 
        # Counters used for missed deadlines and completed runs
        self.missed = 0
        self.completed = 0
    


    def run(self, currentTime):
        """Simulates a run of the task by preventing the system from running another task"""
        self.startTime = currentTime
        self.isRunning = True

    def stop(self, currentTime, computeUnits):
        """Stops the task that is currently running"""
        if self.isRunning == True:
            self.isRunning = False
            self.runTime += computeUnits - self.startTime
            if self.runTime + 0.1 >= self.C:                # Check if task is finished
                if currentTime > self.nextD:                # Check if deadline was missed
                    self.missed += 1
                self.completed += 1
                self.reset(currentTime)
                return 1       


    def checkState(self, currentTime, computeUnits):
        """Handles the state of the task: Releases it if time, or check if it has finished running or missed deadlines"""
        
        if self.released == False:                          # Waiting to be released
            if self.nextRelease <= currentTime:
                self.released = True
                self.lastRelease += self.T
                return 2                                    # Returns 2 in event that task needs to be released
        else:                     
            if self.isRunning:                              # Task is released so check deadlines
                if self.runTime + (computeUnits - self.startTime) + 0.1 >= self.C:          # Task has completed, check if it missed deadline
                    latenessCalc = False
                    if self.lastMiss == True:
                        if self.worstMiss < currentTime - self.lastMissTime:
                            self.worstMiss = currentTime - self.lastMissTime
                        self.missTime += currentTime - self.lastMissTime
                        self.lastMiss = False
                        latenessCalc = True
                    if currentTime > self.nextD:
                        self.missed += 1
                        if self.worstMiss < currentTime - self.nextD:
                            self.worstMiss = currentTime - self.nextD
                        if latenessCalc == False:
                            self.missTime += currentTime - self.nextD
                        self.partialMiss += 1
                    self.completed += 1
                    self.reset(currentTime)
                    return 1                                # Returns 1 in event that task has completed running
            else:
                if currentTime > self.nextD:
                    self.missed += 1
                    if self.lastMiss == False:
                        self.lastMiss = True
                        self.lastMissTime = currentTime
                    self.reset(currentTime)
                    return -1                               # Returns -1 in event that deadline has been missed while idling
        return 0                                            # Returns 0 if nothing needs to be done


    def reset(self, currentTime):
        """Resets task values and calculates the next release and deadline for the task based on current time"""
        self.released = False
        self.isRunning = False
        self.nextRelease = self.lastRelease + self.T
        self.nextD = self.nextRelease + self.D  
        self.runTime = 0

    def clear(self):
        """Clears all values ready for a new run of the simulator"""
        self.lastRelease = 0
        self.nextRelease = 0
        self.nextD = self.D
        self.runTime = 0
        self.released = False
        self.isRunning = False
        self.missTime = 0
        self.worstMiss = 0
        self.partialMiss = 0
        self.lastMiss = False
        self.lastMissTime = 0
        self.missed = 0
        self.completed = 0



def randomSchedule(taskList, releaseList, currentTime, taskLaxity, overhead = 0):
    """Randomly selects a task in the release list and runs it"""
    selected = releaseList[random.randint(0, len(releaseList)-1)]
    return selected, turboDecision(selected, taskList, currentTime, taskLaxity), overhead

def EDFschedule(taskList, releaseList, currentTime, taskLaxity,  overhead = 0.1):
    """Selects the task with the nearest relative deadline to run"""
    deadline = -1
    selected = -1
    for i in range(len(releaseList)):
        if deadline == -1:
            deadline = taskList[releaseList[i]].nextD
            selected = releaseList[i]
        else:
            if taskList[releaseList[i]].nextD < deadline:
                deadline = taskList[releaseList[i]].nextD
                selected = releaseList[i]
    return selected, turboDecision(selected, taskList, currentTime, taskLaxity), overhead

def turboDecision(taskNum, taskList, currentTime, taskLaxity):
    """Assesses time left until a tasks deadline, and reccomends either standard speed or turbo speed based on the taskLaxity threshold"""
    workLeft = taskList[taskNum].C - taskList[taskNum].runTime
    timeUntilD = taskList[taskNum].nextD - currentTime
    if workLeft  <= timeUntilD * taskLaxity:
        return False
    else:                                       
        return True

def generateTaskSet(n, U, minT, maxT, minL, maxL, nLowLax, defaultLL = 0.2, defaultHL = 0.4):
    """Generates a list of Task objects based on parameters and U generated from UUniFast"""
    taskSet = []
    util = uuf.UUniFastDiscard(n, U, 1)
    for i in range(n):
        T = random.randint(minT,maxT)
        if int(util[0][i] * T) == 0:
            C = 1
        else:
            C = int(util[0][i] * T)
        if nLowLax > 0:
            L = random.uniform(defaultLL, defaultHL)
            nLowLax -= 1
        else:
            L = random.uniform(minL, maxL)
        if T * L < C:
            D = C                                   # If deadline will be less than C time, set C time to = D
        else:
            D = int(T * L)              
        taskSet.append(Task(T, D, C))
    return taskSet

def taskSimulator(schedulingAlgorithm, nTicks, tasks, turboLaxity, turboSpeed, preemption):
    """Take a set list of tasks and attempt to schedule them using a scheduling function"""

    released = []
    running = -1                                    # -1: Not running, else it is the number of the running task
    idling = True
    turbo = False
    idleTicks = 0
    turboTicks = 0 
    speedFactor = 1.0
    workDone = 0
    ticks = 0
    overhead = 0
    
    while ticks < nTicks:                           # Main loop - simulate for nTicks time
        thisLoopSpeed = speedFactor
        tickWork = 0
        if running != -1 and tasks[running].C - (tasks[running].runTime + (workDone - tasks[running].startTime)) < 1:   # If task is running and has completed
            thisLoopSpeed = 1.0
            speedFactor = 1.0
            tickWork = tasks[running].C - (tasks[running].runTime + (workDone - tasks[running].startTime))              # Only do work up to the tasks deadline
            if turbo == True:
                turboTicks += tickWork/speedFactor
        elif running != -1:
            tickWork = 1 * speedFactor              # Apply computation 
            if turbo == True:
                turboTicks += 1
        if idling == True:
            idleTicks += 1
            tickWork = 1
        workDone += tickWork
        
        i = 0
        while i < len(tasks):                       # Check all tasks for releases and deadline misses
            state = tasks[i].checkState(ticks, workDone)
            if state == 2:
                released.append(i)                  # Task needs to be released
                if preemption == True:              # If in preemption mode, signal that task needs to be stopped
                    if running != -1 and tasks[running].stop(ticks, workDone) == 1:
                        released.remove(running)
                    running = -1
            elif state == -1:
                released.remove(i)                  # Task needs to be unreleased, then check task again                            
            elif state == 1:
                released.remove(i)                  # Task needs to be unreleased, running has finished. then check task again
                running = -1
            elif state == 0:
                i += 1                              # Nothing needs to be done to the task, move to next



        ticks += tickWork/thisLoopSpeed  
        if running == -1:                           # If no task running, choose next task
            if len(released) > 0:  
                running, turbo, oh = schedulingAlgorithm(tasks, released, ticks, turboLaxity)
                overhead += oh
                if turbo == True:
                    speedFactor = turboSpeed        # Activate turbo mode if releaser recommends it
                else:
                    speedFactor = 1.0
                workDone = ticks
                tasks[running].run(ticks)                
                idling = False
            else:
                idling = True                       # No tasks released so idle at regular speed
                turbo = False
                speedFactor = 1.0
    return idleTicks, turboTicks, overhead

def results(taskSet, idling, turbo,nTicks, row):
    """Outputs results for last task set to a csv file"""
    totalMissed = 0
    totalCompleted = 0
    for i in range(len(taskSet)):
        totalMissed += taskSet[i].missed
        totalCompleted += taskSet[i].completed
        averageMiss = 0
        if taskSet[i].missed != 0:
            averageMiss = math.ceil(taskSet[i].missTime/taskSet[i].missed)
        for v in (taskSet[i].missed, taskSet[i].completed, taskSet[i].partialMiss, averageMiss, taskSet[i].worstMiss):
            row.append(v)
    return totalCompleted, totalMissed, idling, turbo
        

def runSimulator(nTasks, U, minT, maxT, minL, maxL, nLowLax, nTicks, taskHeadroom, turboSpeed, preemption, scheduler1, scheduler2):
    """Function to handle a running of the task simulator, using two competing algorithms"""
    tasks = generateTaskSet(nTasks, U, minT, maxT, minL, maxL, nLowLax)                                         # Generate utilizations using UUniFast
    power = []
    utils = [" "]
    for task in tasks:
        utils.append(task.U)
    idling, turbo, overhead = taskSimulator(scheduler1, nTicks, tasks, taskHeadroom, turboSpeed, preemption)    # Run the simulator using one algorithm and save parameters 
    power.append(calcPowerUnits(idling, turbo, turboSpeed, overhead))                                           
    summary = []
    taskData = []
    for v in results(tasks, idling, turbo, nTicks, taskData):                                                   # Construct an list of task set values to output to csv (Deadline misses, power usage, utilizations etc
        summary.append(v)
    for task in tasks:
        task.clear()
    idling, turbo, overhead = taskSimulator(scheduler2, nTicks, tasks, taskHeadroom, turboSpeed, preemption)    # Run the simulator using the second algorithm
    power.append(calcPowerUnits(idling, turbo, turboSpeed, overhead))
    for v in results(tasks, idling, turbo, nTicks, taskData):
        summary.append(v)
    return utils+summary+taskData+power+winner(summary[0],summary[1], power[0],summary[4],summary[5], power[1]) # Return the summary for the task set in a list, containing results for both algorithms


def calcPowerUnits(idle, turbo, turboSpeed, overhead):
    """Calculates power units consumed from idle and turbo ticks"""
    if turboSpeed == 1.2:
        return (10000 - idle - turbo)+(idle*0.2)+(turbo*1.44)+overhead
    elif turboSpeed == 1.5:
        return (10000 - idle - turbo)+(idle*0.2)+(turbo*2.5)+overhead
    elif turboSpeed == 1.0:
        return (10000 - idle - turbo)+(idle*0.2)+(turbo*1.0)+overhead
    elif turboSpeed == 2.0:
        return (10000 - idle - turbo)+(idle*0.2)+(turbo*5)+overhead

def winner(EDFcompleted, EDFmissedD, EDFpower, randCompleted, randMissedD, randPower):
    """ Decides which scheme performed favourably. Algorithm automatically loses if missed deadlines are > 1% of number of task completions
    and it missed more than the other (Loses because ineffective scheduling). """
    if (randMissedD*100)/randCompleted > 0.1 and randMissedD>EDFmissedD:  #EDF Wins: Random ineffective scheduling (randMissedD*100)/randCompleted > 0.1
        return [1,0,"RandomIneffective"]
    elif (EDFmissedD*100)/EDFcompleted > 0.1 and EDFmissedD>randMissedD:  #Random Wins: EDF ineffective scheduling (EDFmissedD*100)/EDFcompleted > 0.1
        return [0,1,"EDFIneffective"]
    elif (randPower < EDFpower) and (randPower*100)/EDFpower <= 99:     #Random Wins: 1% or better power economy, effective scheduling
        return [0,1,"Random>Power"]
    elif (EDFpower < randPower) and (EDFpower*100)/randPower <= 99:     #EDF Wins: 1% or better power economy, effective scheduling
        return [1,0,"EDF>Power"]
    else:
        if random.randint(0,1) == 0:    #Tie, randomly choose a winner
            return [1,0,"Tie"]
        else:
            return [0,1,"Tie"]

#constants
preemption = True
nTicks = 10000				# Number of ticks a task set is simulated for
nTasks = 5					# Number of tasks in set
iterations = 100            # Handles # of iterations. If more than 100, use pypy implementation
taskHeadroom = 0.75         # Turbo will kick in if task has 25% laxity of its deadline
minT = 20					# Minimum task period
maxT = 100					# Maximum task period
minL = 1					# Minimum task laxity
maxL = 1					# Maximum task laxity
nLowLax = 0					# Number of tasks with a very low laxity
turboSpeed = 2				# Speed of the processor when turbo is activated
U = 0.75					# Utilization of the task set 0 <= U <= 1.


#Run the simulator and save results to a local csv file
for i in range(1):
    path ='results_U='+str(U)+'.csv'
    with open(path, 'wb') as csvfile:
        csvwriter = csv.writer(csvfile, dialect='excel')
        csvwriter.writerow([" ", "U1","U2","U3","U4","U5","EDFCompleted","EDFMissed", "EDFidle", "EDFturbo","RSCompleted","RSMissed", "RSidle", "RSturbo", "T1Missed", "T1Completed", "LM", "AL", "WL", "T2Missed","T2Completed", "LM", "AL", "WL", "T3Missed","T3Completed","LM", "AL", "WL", "T4Missed","T4Completed","LM", "AL", "WL", "T5Missed","T5Completed","LM", "AL", "WL", "T1Missed", "T1Completed", "LM", "AL", "WL", "T2Missed","T2Completed", "LM", "AL", "WL", "T3Missed","T3Completed","LM", "AL", "WL", "T4Missed","T4Completed","LM", "AL", "WL", "T5Missed","T5Completed","LM", "AL", "WL","EDFPower","RandPower","EDFwin","RandWin","Reason","\n"])
        for i in range(iterations):
            csvwriter.writerow(runSimulator(nTasks, U, minT, maxT, minL, maxL, nLowLax, nTicks, taskHeadroom, turboSpeed, preemption, EDFschedule, randomSchedule))
print "File written to local directory"

#Other configuration examples:
                
#Overall Laxity: Release(Period)&Deadline between x & y
#minL = 0.7
#maxL = 0.7
#nLowLax = 0
#turboSpeed = 1.2

#2 tasks Very low laxity, rest uniform
#minL = 1.0
#maxL = 1.0
#nLowLax = 2
#turboSpeed = 1.2

#turbo boost speed
#minL = 1.0
#maxL = 1.0
#nLowLax = 0
#turboSpeed = 1.5





