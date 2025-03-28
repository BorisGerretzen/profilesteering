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


class HeatPump(AbstractDevice):
    def __init__(self):
        self.profile = []  # x_m in the PS paper
        self.candidate = []  # ^x_m in the PS paper

        # Device specific params
        self.capacity = 14000  # in Wtau, converted in electricity equivalent
        self.max_power = 5000  # in W, electricity
        self.min_power = 0
        self.initialSoC = 0.5 * self.capacity

        # Importing the optimization library
        self.opt = opt.optAlg.OptAlg()

    def init(self, p: list[float]) -> PyCtxt:
        # Heat demand
        # We create a random list of power values, but it can be any list
        self.heatdemand = []
        for i in range(0, len(p)):
            self.heatdemand.append(self.max_power * 1.5 * random.random())

        # Create an initial planning.
        # Need to set the initial profile to get the correct length:
        self.profile = [0] * len(p)

        # We can use the planning function in a local fashion with a zero profile to get a plan
        # Another option would be to use a greedy strategy to plan the profile with greedy charging: asap
        self.plan(p)  # Create an initial plan
        self.accept()  # Accept it, such that self.profile is set

        return self.calculate_private_representation(self.profile)

    def plan(self, d: list[float]) -> float:
        # desired is "d" in the PS paper
        p_m = list(map(operator.sub, self.profile, d))  # p_m = x_m - d

        # Call the magic
        # Function prototype:
        # bufferPlanning(	self, desired, targetSoC, initialSoC, capacity, demand, chargingPowers, powerMin = 0, powerMax = 0,
        #					powerLimitsLower = [], powerLimitsUpper = [], reactivePower = False, prices = [], profileWeight = 1)

        self.candidate = self.opt.bufferPlanning(p_m,
                                                 self.initialSoC,
                                                 self.initialSoC,
                                                 self.capacity,
                                                 self.heatdemand,
                                                 [], self.min_power, self.max_power,
                                                 [], [],
                                                 False,
                                                 [],
                                                 1)
        # We set the target equal to the initial SoC. Note that more clever options based on the desired profile are possible!!!

        # Calculate the improvement by this device:
        e_m = np.linalg.norm(np.array(self.profile) - np.array(p_m)) - np.linalg.norm(
            np.array(self.candidate) - np.array(p_m))

        # Return the improvement
        # print("Improvement: ", self, e_m)
        return e_m

    def accept(self) -> PyCtxt | None:
        # We are chosen as winner, replace the profile:
        diff = list(map(operator.sub, self.candidate, self.profile))
        self.profile = list(self.candidate)

        # Note we can send the difference profile only as incremental update
        return diff