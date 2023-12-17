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
import time

import Pyfhel

from crypto import HE, PrivacySchemes, PRIVACY_SCHEME


def _get_sum(profiles: list) -> list[float]:
    """
    Get the sum of the profiles
    :type profiles: list[Pyfhel.PyCtxt] | list[list[float]]
    :param profiles: list of profiles
    :return: sum of the profiles
    """
    if PRIVACY_SCHEME == PrivacySchemes.HOMOMORPHIC:
        if not isinstance(profiles[0], Pyfhel.PyCtxt):
            raise TypeError("Profiles must be a list of Pyfhel.PyCtxt when using homomorphic encryption")
        return sum(profiles)
    elif PRIVACY_SCHEME == PrivacySchemes.DIFFERENTIAL:
        if not isinstance(profiles[0], tuple) or not isinstance(profiles[0][0], list) or not isinstance(profiles[0][0][0], float):
            raise TypeError("Profiles must be a nested list of floats when using differential privacy")
        real_sum = list(map(sum, zip(*[profile[1] for profile in profiles])))
        noisy_sum = list(map(sum, zip(*[profile[0] for profile in profiles])))

        # plot the real sum and the noisy sum
        import matplotlib.pyplot as plt
        plt.plot(real_sum, label="real sum")
        plt.plot(noisy_sum, label="noisy sum")
        plt.plot(list(map(operator.sub, real_sum, noisy_sum)), label="difference")

        plt.legend()
        plt.show()

        return noisy_sum


class ProfileSteering:
    def __init__(self, devices):
        self.encrypted_sum = None
        self.devices = devices
        self.p = []  # p in the PS paper
        self.x = []  # x in the PS paper

    def _decrypt_sum(self) -> list[float]:
        """
        Decrypt the encrypted sum and set the value of x
        :return: None
        """
        if PRIVACY_SCHEME == PrivacySchemes.HOMOMORPHIC:
            # we have to trim the decrypted sum to the length of p because CKKS pads it to 2**13
            return list(HE.decrypt(self.encrypted_sum)[:len(self.p)])
        elif PRIVACY_SCHEME == PrivacySchemes.DIFFERENTIAL:
            return self.encrypted_sum

    def init(self, p):
        # Set the desired profile and reset xrange
        self.p = list(p)
        self.x = [0] * len(p)

        # Ask all devices to propose an initial planning
        initial_profiles = [device.init(p) for device in self.devices]
        self.encrypted_sum = _get_sum(initial_profiles)
        self.x = self._decrypt_sum()

        return self.x

    def iterative(self, e_min, max_iters):
        # Iterative Loop
        for i in range(0, max_iters):  # Note we deviate here slightly by also definint a maximum number of iterations
            t1 = time.time()
            # Init
            best_improvement = 0
            best_device = None

            # difference profile
            d = list(map(operator.sub, self.x, self.p))  # d = x - p

            # request a new candidate profile from each device
            for device in self.devices:
                improvement = device.plan(d)
                if improvement > best_improvement:
                    best_improvement = improvement
                    best_device = device

            # Now set the winner (best scoring device) and update the planning
            if best_device is not None:
                diff = best_device.accept()
                self.x = list(map(operator.sub, self.x, diff))

            t2 = time.time()
            time_diff = t2 - t1
            print("Iteration", i, "-- Winner", best_device, "Improvement", best_improvement, "Time", round(time_diff, 5))
            # print("Overall Profile", self.x)

            # Now check id the improvement is good enough
            if best_improvement < e_min:
                break  # Break the loop

        return self.x  # Return the profile
