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
    def exists(self, id: str) -> bool:
        pass

    @abstractmethod
    def update_state(self, r: Request, state: State, msg: str = None):
        pass

    @abstractmethod
    def reply_failed(self) -> int:
        pass

    @abstractmethod
    def get_statistics(self) -> (int, int, int, int, int):
        pass
