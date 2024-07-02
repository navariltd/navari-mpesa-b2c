import json
from dataclasses import asdict, dataclass


@dataclass(init=True, frozen=True)
class B2CRequestDefinition:
    """Dataclass bearing the Request Data sent to Daraja API"""

    Setting: str
    ConsumerKey: str
    ConsumerSecret: str
    OriginatorConversationID: str
    InitiatorName: str
    SecurityCredential: str
    CommandID: str
    Amount: str
    PartyA: str
    PartyB: str
    Remarks: str
    Occassion: str

    def to_dict(self, with_dict: dict[str, str] | None = None) -> dict:
        """Returns a Dictionary representation of the Dataclass, excluding fields Setting,
        ConsumerKey, and ConsumerSecret

        Args:
            with_dict (dict[str, str] | None): Additional dict like object to add to the
            resultant dictionary

        Returns:
            dict: The dictionary representation of the dataclass
        """
        data_dict = asdict(self)
        exclude_fields = {"Setting", "ConsumerKey", "ConsumerSecret"}
        filtered_dict = {k: v for k, v in data_dict.items() if k not in exclude_fields}

        if isinstance(with_dict, dict):
            filtered_dict.update(with_dict)

        return filtered_dict

    def to_json(self, with_dict: dict[str, str] | None = None) -> str:
        """Returns a JSON representation of the dataclass, excluding fields Setting,
        ConsumerKey, and ConsumerSecret

        Args:
            with_dict (dict[str, str] | None): Additional dict like object to add to the
            resultant JSON string

        Returns:
            str: The JSON representation of the dataclass values
        """
        return json.dumps(self.to_dict(with_dict))
