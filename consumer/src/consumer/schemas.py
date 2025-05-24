from pydantic_avro.base import AvroBase

class Message(AvroBase):
    username: str
    to_user: str
    text: str
