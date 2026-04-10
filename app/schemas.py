from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from decimal import Decimal


# ============================================================================
# INVOICE SCHEMAS
# ============================================================================

class InvoiceBase(BaseModel):
    customer_id: UUID
    invoice_number: str
    amount: Decimal
    currency: str = "USD"
    issue_date: date
    due_date: date
    status: str = "unpaid"


class InvoiceCreate(InvoiceBase):
    company_id: UUID


class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    payment_date: Optional[date] = None
    paid_amount: Optional[Decimal] = None


class InvoiceResponse(InvoiceBase):
    id: UUID
    company_id: UUID
    payment_date: Optional[date]
    paid_amount: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# PURCHASE ORDER SCHEMAS
# ============================================================================

class PurchaseOrderBase(BaseModel):
    vendor_id: UUID
    po_number: str
    amount: Decimal
    currency: str = "USD"
    order_date: date
    scheduled_payment_date: date
    vendor_payment_terms: Optional[int] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    company_id: UUID


class PurchaseOrderResponse(PurchaseOrderBase):
    id: UUID
    company_id: UUID
    status: str
    payment_date: Optional[date]
    paid_amount: Decimal
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# PROJECT MILESTONE SCHEMAS
# ============================================================================

class ProjectMilestoneBase(BaseModel):
    project_id: UUID
    customer_id: UUID
    milestone_name: str
    contract_amount: Decimal
    milestone_amount: Decimal
    currency: str = "USD"
    scheduled_completion: Optional[date] = None
    completion_percentage: int = 0


class ProjectMilestoneCreate(ProjectMilestoneBase):
    company_id: UUID


class ProjectMilestoneResponse(ProjectMilestoneBase):
    id: UUID
    company_id: UUID
    status: str
    actual_completion: Optional[date]
    scheduled_invoice_date: Optional[date]
    actual_invoice_date: Optional[date]
    invoice_generated: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# SALES OPPORTUNITY SCHEMAS
# ============================================================================

class SalesOpportunityBase(BaseModel):
    customer_id: UUID
    opportunity_name: str
    opportunity_amount: Decimal
    currency: str = "USD"
    stage: str
    probability: Optional[int] = None
    expected_close_date: Optional[date] = None


class SalesOpportunityCreate(SalesOpportunityBase):
    company_id: UUID


class SalesOpportunityResponse(SalesOpportunityBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# FORECAST SCHEMAS
# ============================================================================

class ARCollectionsForecastBase(BaseModel):
    invoice_id: UUID
    predicted_payment_date: date
    confidence_score: Decimal
    amount: Decimal
    currency: str = "USD"
    key_factors: Optional[Dict[str, Any]] = None


class ARCollectionsForecastCreate(ARCollectionsForecastBase):
    company_id: UUID
    model_name: str = "XGBoost_AR"
    model_version: str = "1.0"


class ARCollectionsForecastResponse(ARCollectionsForecastBase):
    id: UUID
    company_id: UUID
    model_name: str
    model_version: str
    prediction_date: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class VendorPaymentForecastBase(BaseModel):
    po_id: UUID
    predicted_payment_date: date
    confidence_score: Decimal
    amount: Decimal
    currency: str = "USD"
    payment_status: str = "flexible"
    constraint_reason: Optional[str] = None
    key_factors: Optional[Dict[str, Any]] = None


class VendorPaymentForecastCreate(VendorPaymentForecastBase):
    company_id: UUID
    model_name: str = "Vendor_Hybrid"
    model_version: str = "1.0"


class VendorPaymentForecastResponse(VendorPaymentForecastBase):
    id: UUID
    company_id: UUID
    model_name: str
    model_version: str
    prediction_date: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectBillingForecastBase(BaseModel):
    milestone_id: UUID
    predicted_invoice_date: date
    predicted_payment_date: Optional[date] = None
    confidence_score: Decimal
    amount: Decimal
    currency: str = "USD"
    completion_probability: Optional[int] = None
    key_factors: Optional[Dict[str, Any]] = None


class ProjectBillingForecastCreate(ProjectBillingForecastBase):
    company_id: UUID
    model_name: str = "Project_Milestone"
    model_version: str = "1.0"


class ProjectBillingForecastResponse(ProjectBillingForecastBase):
    id: UUID
    company_id: UUID
    model_name: str
    prediction_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class SalesPipelineForecastBase(BaseModel):
    opportunity_id: UUID
    predicted_close_date: date
    predicted_invoice_date: date
    win_probability: int
    confidence_score: Decimal
    amount: Decimal
    currency: str = "USD"
    key_factors: Optional[Dict[str, Any]] = None


class SalesPipelineForecastCreate(SalesPipelineForecastBase):
    company_id: UUID
    model_name: str = "Sales_Pipeline"
    model_version: str = "1.0"


class SalesPipelineForecastResponse(SalesPipelineForecastBase):
    id: UUID
    company_id: UUID
    model_name: str
    prediction_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# CASH EVENT SCHEMAS
# ============================================================================

class CashEventBase(BaseModel):
    event_date: date
    event_type: str  # inflow, outflow
    cash_category: str  # ar_collection, vendor_payment, etc.
    amount_original: Decimal
    currency_original: str
    amount_base: Decimal
    base_currency: str
    confidence_score: Decimal
    source_id: UUID
    source_type: str


class CashEventCreate(CashEventBase):
    company_id: UUID


class CashEventResponse(CashEventBase):
    id: UUID
    company_id: UUID
    exchange_rate: Optional[Decimal]
    is_duplicate: bool
    duplicate_of: Optional[UUID]
    forecast_accuracy: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UnifiedCashForecast(BaseModel):
    """Unified cash forecast combining all sources"""
    forecast_date: date
    total_inflows: Decimal
    total_outflows: Decimal
    net_cash_position: Decimal
    currency: str
    
    inflow_breakdown: Dict[str, Decimal]
    outflow_breakdown: Dict[str, Decimal]
    
    confidence_score: Decimal
    events: List[CashEventResponse]


# ============================================================================
# FEATURE STORE SCHEMAS
# ============================================================================

class CustomerFeaturesBase(BaseModel):
    avg_days_to_pay: Optional[Decimal]
    median_days_to_pay: Optional[Decimal]
    payment_std_dev: Optional[Decimal]
    on_time_payment_rate: Optional[Decimal]
    late_payment_frequency: Optional[int]
    recent_avg_days_to_pay: Optional[Decimal]
    recent_payment_consistency_score: Optional[Decimal]
    overdue_invoice_count: int = 0
    total_overdue_amount: Decimal = 0
    credit_risk_score: Optional[Decimal]
    invoice_count_last_3m: Optional[int]
    avg_invoice_amount: Optional[Decimal]


class CustomerFeaturesResponse(CustomerFeaturesBase):
    id: UUID
    company_id: UUID
    customer_id: UUID
    calculated_at: datetime
    
    class Config:
        from_attributes = True


class VendorFeaturesBase(BaseModel):
    avg_days_to_deliver: Optional[Decimal]
    delivery_consistency_score: Optional[Decimal]
    standard_terms: Optional[int]
    avg_actual_payment_days: Optional[Decimal]
    early_payment_tendency: Optional[bool]
    supply_risk_score: Optional[Decimal]
    reliability_score: Optional[Decimal]
    po_count_last_3m: Optional[int]
    avg_po_amount: Optional[Decimal]


class VendorFeaturesResponse(VendorFeaturesBase):
    id: UUID
    company_id: UUID
    vendor_id: UUID
    calculated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# RECOMMENDATION SCHEMAS
# ============================================================================

class RecommendationBase(BaseModel):
    recommendation_type: str
    title: str
    description: Optional[str] = None
    cash_impact_amount: Decimal
    cash_impact_direction: str
    feasibility_score: Decimal
    implementation_effort: str
    implementation_timeframe: Optional[str] = None
    priority_score: Decimal
    affected_entities: Optional[Dict[str, Any]] = None
    required_actions: Optional[Dict[str, Any]] = None


class RecommendationCreate(RecommendationBase):
    company_id: UUID


class RecommendationUpdate(BaseModel):
    status: Optional[str] = None


class RecommendationResponse(RecommendationBase):
    id: UUID
    company_id: UUID
    ranking: Optional[int]
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RecommendationList(BaseModel):
    total_count: int
    recommendations: List[RecommendationResponse]
    total_potential_cash_impact: Decimal


# ============================================================================
# MASTER DATA SCHEMAS
# ============================================================================

class CompanyBase(BaseModel):
    company_name: str
    base_currency: str = "USD"
    fiscal_year_start: int = 1


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class CustomerBase(BaseModel):
    customer_name: str
    customer_code: Optional[str] = None
    country: Optional[str] = None
    credit_limit: Optional[Decimal] = None


class CustomerCreate(CustomerBase):
    company_id: UUID


class CustomerResponse(CustomerBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class VendorBase(BaseModel):
    vendor_name: str
    vendor_code: Optional[str] = None
    country: Optional[str] = None
    payment_terms: Optional[int] = None


class VendorCreate(VendorBase):
    company_id: UUID


class VendorResponse(VendorBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    project_name: str
    project_code: Optional[str] = None
    customer_id: UUID
    total_contract_value: Decimal
    currency: str = "USD"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class ProjectCreate(ProjectBase):
    company_id: UUID


class ProjectResponse(ProjectBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class ForecastAccuracyResponse(BaseModel):
    forecast_type: str
    total_forecasts: int
    mae: Decimal  # Mean Absolute Error in days
    rmse: Decimal  # Root Mean Squared Error
    accuracy_rate: Decimal  # percentage
    amount_mae: Optional[Decimal]  # Amount prediction error


class DashboardMetrics(BaseModel):
    """High-level dashboard metrics"""
    total_forecasted_cash_inflow: Decimal
    total_forecasted_cash_outflow: Decimal
    net_position: Decimal
    forecast_confidence: Decimal
    
    top_5_recommendations: List[RecommendationResponse]
    forecast_accuracy: ForecastAccuracyResponse
    
    forecast_horizon_days: int
    as_of_date: date


class HealthCheckResponse(BaseModel):
    status: str
    message: str
    database_connected: bool
    timestamp: datetime