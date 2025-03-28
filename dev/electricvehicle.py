# Copyright 2023 University of Twente

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import operator
import random
import numpy as np
import opt.optAlg

from dev.abstract_device import AbstractDevice
from crypto import HE
from Pyfhel import PyCtxt


class ElectricVehicle(AbstractDevice):
    def __init__(self):
        self.profile = []  # x_m in the PS paper
        self.candidate = []  # ^x_m in the PS paper

        # Intervallength in seonds
        self.intervalLength = 900

        # Device specific params
        self.capacity = 40000  # Wh

        self.powers = [0, 3000, 4000, 5000, 6000, 7000, 8000]  # Charging powers supported by the EV in Watt
        # NOTE: In continuous mode it will select only the first and last element, any power inbetween is possible
        # NOTE: V2G is supported!

        # Set the following to True to use discrete mode optimization:
        self.discrete = False

        # Connection time of the EV in intervals
        # using intervals of 15 mintues for one day, e.g. 96 in total
        self.startTime = random.randint(7 * 4, 12 * 4)  # Random connection time (15 minute intervals used here)
        self.endTime = random.randint(15 * 4, 22 * 4)  # Random departure time (15 minute intervals used here)

        # Energy demand by the EV
        self.chargeRequest = random.randint(4000, 22000)  # Wh
        self.initialSoC = self.capacity - self.chargeRequest
        assert (self.initialSoC >= 0)
        # Note: Ensure that the EV can be charged in time! (time in hours * maximum charge power!)

        # Importing the optimization library
        self.opt = opt.optAlg.OptAlg()

    def init(self, p: list[float]) -> PyCtxt:
        # Create an initial planning.
        # Need to set the initial profile to get the correct length:
        self.profile = [0] * len(p)

        # We can use the planning function in a local fashion with a zero profile to get a plan
        # Another option would be to use a greedy strategy to plan the profile with greedy charging: asap
        self.plan(p)  # Create an initial plan
        self.accept()  # Accept it, such that self.profile is set

        return self.calculate_private_representation(self.profile)

    # Receiving a plan request from the Profile Steering algorithm
    def plan(self, d: list[float]) -> float:
        # desired is "d" in the PS paper
        p_m = list(map(operator.sub, self.profile, d))  # p_m = x_m - d

        # Call the magic

        # CONTINUOUS VARIANT
        if not self.discrete:
            # Function prototype:
            # bufferPlanning(	self, desired, targetSoC, initialSoC, capacity, demand, chargingPowers, powerMin = 0, powerMax = 0,
            #					powerLimitsLower = [], powerLimitsUpper = [], reactivePower = False, prices = [], profileWeight = 1)

            profile = self.opt.bufferPlanning(p_m[self.startTime:self.endTime],
                                              self.capacity,
                                              self.initialSoC,
                                              self.capacity,
                                              [0] * len(p_m[self.startTime:self.endTime]),  # Static losses, not used
                                              [], self.powers[0], self.powers[1],
                                              [], [],
                                              False,
                                              [],
                                              1)
        # We set the target equal to the initial SoC. Note that more clever options based on the desired profile are possible!!!

        # DISCRETE VARIANT:
        else:
            # Function prototype:
            # discreteBufferPlanningPositive(self, desired, chargeRequired, chargingPowers, powerLimitsUpper = [], prices = None, beta = 1):
            profile = self.opt.discreteBufferPlanningPositive(p_m[self.startTime:self.endTime],
                                                              # We only need the section at which the EV is connected
                                                              self.chargeRequest * int(3600 / self.intervalLength),
                                                              # We need to convert this in "wattTau" instead of WattHours.
                                                              self.powers,
                                                              [],
                                                              None,
                                                              1)

        self.candidate = [0] * len(p_m)  # Create an empty vector
        # Now add the optimized profile at the right indices of the vector
        for i in range(self.startTime, self.endTime):
            self.candidate[i] = profile[i - self.startTime]

        # Calculate the improvement by this device:
        e_m = np.linalg.norm(np.array(self.profile) - np.array(p_m)) - np.linalg.norm(
            np.array(self.candidate) - np.array(p_m))

        # Return the improvement
        # print("Improvement: ", self, e_m)
        return e_m

    # Accept a profile
    def accept(self) -> PyCtxt | None:
        # We are chosen as winner, replace the profile:
        diff = list(map(operator.sub, self.candidate, self.profile))
        self.profile = list(self.candidate)

        # Note we can send the difference profile only as incremental update
        return diff
