"""Data contracts. The extraction schema deliberately has no field for risk: the LLM can't set the score."""
from typing import Literal, Optional

from pydantic import BaseModel, Field

FlagType = Literal["vague_location", "reschedule", "hesitation", "third_party_receiver", "other"]
Language = Literal["ar", "fr", "derja_arabic_script", "derja_latin", "mixed"]
Tone = Literal["confident", "neutral", "hesitant", "hostile"]


class RedFlag(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    type: FlagType


class Flags(BaseModel):
    language: Language = "mixed"
    address_specificity: int = Field(ge=0, le=3)
    has_landmark: bool = False
    red_flags: list[RedFlag] = Field(default_factory=list)
    tone: Tone = "neutral"
    reschedule_requested: bool = False


class Order(BaseModel):
    order_id: str
    created_at: str
    governorate: str
    zone_tier: Literal["urban", "peri-urban", "remote"]
    address_text: str = Field(default="", max_length=1000)
    note_text: str = Field(default="", max_length=1000)
    product_category: str
    value_tnd: float = Field(gt=0)
    item_count: int = Field(ge=1, le=20)
    channel: Literal["facebook", "instagram", "website"]
    is_first_order: bool
    prior_orders: int = Field(ge=0)
    prior_refusals: int = Field(ge=0)


class Extraction(BaseModel):
    flags: Optional[Flags]
    failed: bool
    source: Literal["llm", "heuristic", "none"]
    cache_hit: bool = False
    latency_ms: int = 0
    error: str = ""


class Score(BaseModel):
    score: float
    tier: Literal["Low", "Med", "High"]
    contribs: dict[str, float]
    action: str
    explanation: str


class Verdict(BaseModel):
    approved: bool
    checks: dict[str, bool] = Field(default_factory=dict)
    reason: str = ""
    source: Literal["llm_judge", "guards", "static_template", "unavailable"] = "llm_judge"


class Draft(BaseModel):
    body: str
    source: Literal["llm", "static_template"]
    attempts: int
    verdict: Verdict
    sendable: bool
