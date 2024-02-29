from pydantic import BaseModel, ConfigDict


class EskizBaseModel(BaseModel):
    """Base model for sankaku JSON responses."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)
