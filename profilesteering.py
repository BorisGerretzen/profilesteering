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

from crypto import HE


class ProfileSteering():
    def __init__(self, devices):
        self.encrypted_sum = None
        self.devices = devices
        self.p = []  # p in the PS paper
        self.x = []  # x in the PS paper

    def _get_decrypt(self) -> None:
        """
        Decrypt the encrypted sum and set the value of x
        :return: None
        """
        # we have to trim the decrypted sum to the length of p because CKKS pads it to 2**13
        self.x = list(HE.decrypt(self.encrypted_sum)[:len(self.p)])

    def init(self, p):
        # Set the desired profile and reset xrange
        self.p = list(p)
        self.x = [0] * len(p)

        # Ask all devices to propose an initial planning
        # In a real setup this would be done by the adder
        self.encrypted_sum = sum([device.init(p) for device in self.devices])

        # Receive the encrypted sum from the adder and decrypt
        self._get_decrypt()

        return self.x

    def iterative(self, e_min, max_iters):
        # Iterative Loop
        for i in range(0, max_iters):  # Note we deviate here slightly by also definint a maximum number of iterations
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
                # Update the encrypted sum, once again in a real setup this would be done by the adder
                self.encrypted_sum = self.encrypted_sum + diff

                # Decrypt the encrypted sum and set the value of x
                self._get_decrypt()

            print("Iteration", i, "-- Winner", best_device, "Improvement", best_improvement)
            # print("Overall Profile", self.x)

            # Now check id the improvement is good enough
            if best_improvement < e_min:
                break  # Break the loop

        return self.x  # Return the profile
