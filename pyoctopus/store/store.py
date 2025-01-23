from abc import abstractmethod

from ..request import Request, State


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
    def get_statistics(self) -> tuple[int, int, int, int, int]:
        pass

    @abstractmethod
    def has_waiting_requests(self) -> bool:
        pass
