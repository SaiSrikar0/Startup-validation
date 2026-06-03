from pydantic import BaseModel, Field

class StartupInputSchema(BaseModel):
    funding_total_usd: float = Field(..., description="Total funding raised in USD", example=150000.0)
    market_size_usd: float = Field(..., description="Target market size in USD", example=5000000.0)
    team_experience_years: int = Field(..., description="Combined experience of founders", example=8)
    country_code: str = Field(..., description="ISO Country Code (e.g., 'USA', 'IND')", example="USA")
    category_code: str = Field(..., description="Industry sector (e.g., 'tech', 'biotech')", example="tech")

class PredictionResponseSchema(BaseModel):
    success_probability: float = Field(..., description="Calculated probability of success (0.0 to 1.0)")
    prediction_label: str = Field(..., description="'Success' or 'Failure'")
    status: str = Field(default="success")