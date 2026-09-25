from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ArticlePair:
    pair_id: str
    left_title: str
    left_summary: str
    right_title: str
    right_summary: str
    same_event: bool
