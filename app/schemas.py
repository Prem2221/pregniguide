from pydantic import BaseModel, Field


class ComparisonRow(BaseModel):
    label: str
    value_a: str
    value_b: str


class Comparison(BaseModel):
    item_a: str
    item_b: str
    rows: list[ComparisonRow]


class StructuredAnswer(BaseModel):
    answer_markdown: str = Field(description="The main answer, in simple language, using markdown formatting and emojis where appropriate")
    comparison: Comparison | None = Field(default=None)
    follow_up_questions: list[str] = Field(default_factory=list, description="2-3 short, relevant follow-up questions the user might naturally ask next")