from pydantic import BaseModel, Field
from typing import List


# -----------------------------------------------------------------------------
# Request Model: What the user sends to our API
# -----------------------------------------------------------------------------
class ResearchRequest(BaseModel):
    """
    Data sent by the user to start a research task.
    """
    query: str = Field(
        ...,
        description="The research question or topic",
        examples=["Compare PostgreSQL, MongoDB and DynamoDB for an e-commerce backend"]
    )


# -----------------------------------------------------------------------------
# Item Model: A single search result item
# -----------------------------------------------------------------------------
class SearchResultItem(BaseModel):
    """
    Represents an individual search source gathered by the Researcher agent.
    """
    sub_question: str = Field(..., description="The sub-question this source helps answer")
    title: str = Field(..., description="Title of the webpage")
    url: str = Field(..., description="Direct link to the source")
    snippet: str = Field(..., description="Text summary/preview from the source")


# -----------------------------------------------------------------------------
# Response Model: What our API sends back to the user
# -----------------------------------------------------------------------------
class ResearchResponse(BaseModel):
    """
    Data returned to the user after running the research workflow.
    In Phase 3, this includes the sub-questions AND live search results.
    """
    status: str = Field(
        ...,
        description="Current status of the research workflow",
        examples=["completed"]
    )
    query: str = Field(
        ...,
        description="Echoes back the research query received"
    )
    sub_questions: List[str] = Field(
        default_factory=list,
        description="The broken-down sub-questions produced by the Planner node"
    )
    search_results: List[SearchResultItem] = Field(
        default_factory=list,
        description="Live web sources gathered by the Researcher node"
    )
    message: str = Field(
        ...,
        description="Human-readable explanation of current status"
    )
