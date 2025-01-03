from abc import abstractmethod

from ..reqeust import Request


class Store:

    @abstractmethod
    def put(self, r: Request) -> bool:
        pass

    @abstractmethod
    def get(self) -> Request | None:
        pass
