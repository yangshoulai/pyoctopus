from abc import abstractmethod

from ..reqeust import Request, State


class Store:

    @abstractmethod
    def put(self, r: Request) -> bool:
        pass

    @abstractmethod
    def get(self) -> Request | None:
        pass

    @abstractmethod
    def update_state(self, r: Request, state: State):
        pass
