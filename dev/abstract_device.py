from abc import ABC, abstractmethod

import numpy as np

from crypto import PRIVACY_SCHEME, PrivacySchemes, HE, DifferentialOptions
from Pyfhel import PyCtxt


class AbstractDevice(ABC):
    @abstractmethod
    def init(self, p: list[float]) -> PyCtxt:
        """
        Creates an initial planning for the device.
        :param p: Desired profile
        :return: Encrypted sum of the planning
        """
        pass

    @abstractmethod
    def plan(self, d: list[float]) -> float:
        """
        Requests a new candidate profile from the device.
        :param d: Difference profile
        :return: Improvement of the candidate profile
        """
        pass

    @abstractmethod
    def accept(self) -> PyCtxt | None:
        """
        Accepts the current candidate profile.
        :return: Encrypted difference between the current candidate profile and the previous profile.
        """
        pass

    @staticmethod
    def calculate_private_representation(p: list[float]) -> tuple[list[float], list[float]] | PyCtxt:
        """
        Calculates the private representation of a profile.
        :param p: Profile
        :return: Private representation of the profile
        """

        if PRIVACY_SCHEME == PrivacySchemes.HOMOMORPHIC:
            return HE.encryptFrac(np.array(p, dtype=np.float64))
        elif PRIVACY_SCHEME == PrivacySchemes.DIFFERENTIAL:
            return list(np.array(p, dtype=np.float64) + np.random.laplace(0, DifferentialOptions['scale'], len(p))), p
        pass