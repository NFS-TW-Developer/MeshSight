from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    status: str = ""
    message: str = ""
    data: T
