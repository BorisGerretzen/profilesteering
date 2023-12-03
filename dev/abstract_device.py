from abc import ABC, abstractmethod

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
