from dataclasses import asdict, dataclass


@dataclass(init=True, frozen=True)
class B2CRequestDefinition:
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

    def to_dict(self) -> dict:
        """Returns a Dictionary representation of the Dataclass, excluding fields Setting, 
        ConsumerKey, and ConsumerSecret

        Returns:
            dict: The dictionary representation
        """
        data_dict = asdict(self)
        exclude_fields = {"Setting", "ConsumerKey", "ConsumerSecret"}
        filtered_dict = {k: v for k, v in data_dict.items() if k not in exclude_fields}
        return filtered_dict
