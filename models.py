from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey, JSON, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, date
import uuid
from database import Base


# ============================================================================
# CORE FINANCIAL DATA MODELS
# ============================================================================

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    status = Column(String(20), default='unpaid', index=True)
    payment_date = Column(Date)
    paid_amount = Column(Numeric(15, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_invoices_company_customer', 'company_id', 'customer_id'),
    )


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    vendor_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    po_number = Column(String(50), unique=True, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')
    order_date = Column(Date, nullable=False)
    scheduled_payment_date = Column(Date, nullable=False, index=True)
    status = Column(String(20), default='pending', index=True)
    payment_date = Column(Date)
    paid_amount = Column(Numeric(15, 2), default=0)
    vendor_payment_terms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_po_company_vendor', 'company_id', 'vendor_id'),
    )


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    milestone_name = Column(String(255), nullable=False)
    contract_amount = Column(Numeric(15, 2), nullable=False)
    milestone_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')
    scheduled_completion = Column(Date)
    actual_completion = Column(Date)
    scheduled_invoice_date = Column(Date, index=True)
    actual_invoice_date = Column(Date)
    invoice_generated = Column(Boolean, default=False)
    invoice_id = Column(UUID(as_uuid=True))
    status = Column(String(20), default='pending', index=True)
    completion_percentage = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SalesOpportunity(Base):
    __tablename__ = "sales_opportunities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    opportunity_name = Column(String(255), nullable=False)
    opportunity_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')
    stage = Column(String(50), nullable=False, index=True)
    probability = Column(Integer)
    expected_close_date = Column(Date, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OtherInflow(Base):
    __tablename__ = "other_inflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    inflow_type = Column(String(50), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')
    description = Column(Text)
    expected_date = Column(Date, nullable=False, index=True)
    status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OperationalExpense(Base):
    __tablename__ = "operational_expenses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    expense_type = Column(String(50), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default='USD')
    frequency = Column(String(20), default='monthly')
    description = Column(Text)
    next_due_date = Column(Date, nullable=False, index=True)
    is_recurring = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# FEATURE STORE MODELS
# ============================================================================

class CustomerFeatures(Base):
    __tablename__ = "customer_features"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    avg_days_to_pay = Column(Numeric(10, 2))
    median_days_to_pay = Column(Numeric(10, 2))
    payment_std_dev = Column(Numeric(10, 2))
    on_time_payment_rate = Column(Numeric(5, 2))
    late_payment_frequency = Column(Integer)
    
    recent_avg_days_to_pay = Column(Numeric(10, 2))
    recent_payment_consistency_score = Column(Numeric(5, 2))
    
    overdue_invoice_count = Column(Integer, default=0)
    total_overdue_amount = Column(Numeric(15, 2), default=0)
    credit_risk_score = Column(Numeric(5, 2), index=True)
    
    invoice_count_last_3m = Column(Integer)
    avg_invoice_amount = Column(Numeric(15, 2))
    
    high_payment_season = Column(String(50))
    low_payment_season = Column(String(50))
    
    calculated_at = Column(DateTime, default=datetime.utcnow)


class VendorFeatures(Base):
    __tablename__ = "vendor_features"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    vendor_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    avg_days_to_deliver = Column(Numeric(10, 2))
    delivery_consistency_score = Column(Numeric(5, 2))
    
    standard_terms = Column(Integer)
    avg_actual_payment_days = Column(Numeric(10, 2))
    early_payment_tendency = Column(Boolean)
    
    supply_risk_score = Column(Numeric(5, 2), index=True)
    reliability_score = Column(Numeric(5, 2))
    
    po_count_last_3m = Column(Integer)
    avg_po_amount = Column(Numeric(15, 2))
    
    calculated_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# FORECAST MODELS
# ============================================================================

class ARCollectionsForecast(Base):
    __tablename__ = "ar_collections_forecast"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    predicted_payment_date = Column(Date, nullable=False, index=True)
    confidence_score = Column(Numeric(5, 2), nullable=False)
    amount = Column(Numeric(15, 2))
    currency = Column(String(3))
    
    model_name = Column(String(100))
    model_version = Column(String(20))
    prediction_date = Column(DateTime, default=datetime.utcnow)
    
    key_factors = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VendorPaymentForecast(Base):
    __tablename__ = "vendor_payment_forecast"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    po_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    predicted_payment_date = Column(Date, nullable=False, index=True)
    confidence_score = Column(Numeric(5, 2), nullable=False)
    amount = Column(Numeric(15, 2))
    currency = Column(String(3))
    
    payment_status = Column(String(20))
    constraint_reason = Column(String(100))
    
    model_name = Column(String(100))
    model_version = Column(String(20))
    prediction_date = Column(DateTime, default=datetime.utcnow)
    
    key_factors = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProjectBillingForecast(Base):
    __tablename__ = "project_billing_forecast"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    milestone_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    predicted_invoice_date = Column(Date, nullable=False, index=True)
    predicted_payment_date = Column(Date)
    confidence_score = Column(Numeric(5, 2), nullable=False)
    amount = Column(Numeric(15, 2))
    currency = Column(String(3))
    
    completion_probability = Column(Integer)
    
    model_name = Column(String(100))
    prediction_date = Column(DateTime, default=datetime.utcnow)
    
    key_factors = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class SalesPipelineForecast(Base):
    __tablename__ = "sales_pipeline_forecast"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    opportunity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    predicted_close_date = Column(Date, nullable=False)
    predicted_invoice_date = Column(Date, nullable=False, index=True)
    win_probability = Column(Integer)
    confidence_score = Column(Numeric(5, 2), nullable=False)
    amount = Column(Numeric(15, 2))
    currency = Column(String(3))
    
    model_name = Column(String(100))
    prediction_date = Column(DateTime, default=datetime.utcnow)
    
    key_factors = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class CashEvent(Base):
    __tablename__ = "cash_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    event_date = Column(Date, nullable=False, index=True)
    event_type = Column(String(20), nullable=False, index=True)
    cash_category = Column(String(50), nullable=False, index=True)
    
    amount_original = Column(Numeric(15, 2))
    currency_original = Column(String(3))
    amount_base = Column(Numeric(15, 2))
    base_currency = Column(String(3))
    exchange_rate = Column(Numeric(10, 6))
    
    confidence_score = Column(Numeric(5, 2))
    source_id = Column(UUID(as_uuid=True))
    source_type = Column(String(50))
    
    is_duplicate = Column(Boolean, default=False)
    duplicate_of = Column(UUID(as_uuid=True))
    
    forecast_accuracy = Column(Numeric(5, 2))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_cash_events_date_range', 'company_id', 'event_date'),
    )


# ============================================================================
# RECOMMENDATIONS MODEL
# ============================================================================

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    recommendation_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    cash_impact_amount = Column(Numeric(15, 2))
    cash_impact_direction = Column(String(20))
    
    feasibility_score = Column(Numeric(5, 2))
    implementation_effort = Column(String(20))
    implementation_timeframe = Column(String(100))
    
    priority_score = Column(Numeric(5, 2), index=True)
    ranking = Column(Integer)
    
    affected_entities = Column(JSON)
    required_actions = Column(JSON)
    
    status = Column(String(20), default='pending', index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# MASTER DATA MODELS
# ============================================================================

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(255), nullable=False)
    base_currency = Column(String(3), default='USD')
    fiscal_year_start = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_code = Column(String(50))
    country = Column(String(100))
    credit_limit = Column(Numeric(15, 2))
    created_at = Column(DateTime, default=datetime.utcnow)


class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    vendor_name = Column(String(255), nullable=False)
    vendor_code = Column(String(50))
    country = Column(String(100))
    payment_terms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    project_name = Column(String(255), nullable=False)
    project_code = Column(String(50))
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    total_contract_value = Column(Numeric(15, 2))
    currency = Column(String(3))
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# AUDIT & ANALYTICS MODELS
# ============================================================================

class ForecastAccuracyLog(Base):
    __tablename__ = "forecast_accuracy_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    forecast_id = Column(UUID(as_uuid=True))
    forecast_type = Column(String(50), index=True)
    predicted_date = Column(Date)
    actual_date = Column(Date)
    
    days_variance = Column(Integer)
    accuracy_percentage = Column(Numeric(5, 2))
    
    amount_predicted = Column(Numeric(15, 2))
    amount_actual = Column(Numeric(15, 2))
    amount_variance = Column(Numeric(5, 2))
    
    logged_at = Column(DateTime, default=datetime.utcnow, index=True)


class ModelPerformance(Base):
    __tablename__ = "model_performance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    model_name = Column(String(100))
    model_version = Column(String(20))
    model_type = Column(String(50))
    
    mae = Column(Numeric(10, 6))
    rmse = Column(Numeric(10, 6))
    r2_score = Column(Numeric(5, 2))
    
    training_samples = Column(Integer)
    evaluation_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)