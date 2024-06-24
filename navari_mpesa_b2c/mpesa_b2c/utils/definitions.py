from dataclasses import dataclass


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
