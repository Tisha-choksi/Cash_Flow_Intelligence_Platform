-- ============================================================================
-- CASH FLOW INTELLIGENCE PLATFORM - PostgreSQL Schema
-- ============================================================================

-- Extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================================
-- 1. CORE FINANCIAL DATA TABLES
-- ============================================================================

-- Invoices (AR Collections source)
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'unpaid', -- unpaid, partially_paid, paid, overdue
    payment_date DATE,
    paid_amount DECIMAL(15, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (customer_id),
    INDEX (status),
    INDEX (due_date)
);

-- Purchase Orders & Vendor Payments
CREATE TABLE purchase_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    vendor_id UUID NOT NULL,
    po_number VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    order_date DATE NOT NULL,
    scheduled_payment_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, received, paid, cancelled
    payment_date DATE,
    paid_amount DECIMAL(15, 2) DEFAULT 0,
    vendor_payment_terms INT, -- days
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (vendor_id),
    INDEX (status),
    INDEX (scheduled_payment_date)
);

-- Project Milestones (Project Billing source)
CREATE TABLE project_milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    project_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    milestone_name VARCHAR(255) NOT NULL,
    contract_amount DECIMAL(15, 2) NOT NULL,
    milestone_amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    scheduled_completion DATE,
    actual_completion DATE,
    scheduled_invoice_date DATE,
    actual_invoice_date DATE,
    invoice_generated BOOLEAN DEFAULT FALSE,
    invoice_id UUID,
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, invoiced, paid
    completion_percentage INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (project_id),
    INDEX (customer_id),
    INDEX (status),
    INDEX (scheduled_invoice_date)
);

-- Sales Opportunities & Pipeline
CREATE TABLE sales_opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    opportunity_name VARCHAR(255) NOT NULL,
    opportunity_amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    stage VARCHAR(50) NOT NULL, -- prospecting, negotiation, proposal, decision, closed_won, closed_lost
    probability INT, -- 0-100
    expected_close_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (customer_id),
    INDEX (stage),
    INDEX (expected_close_date)
);

-- Other Cash Inflows (Loans, Grants, Refunds)
CREATE TABLE other_inflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    inflow_type VARCHAR(50) NOT NULL, -- loan, grant, refund, investment, other
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    description TEXT,
    expected_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, received
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (company_id),
    INDEX (expected_date)
);

-- Operational Expenses (Salaries, Taxes, Recurring Costs)
CREATE TABLE operational_expenses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    expense_type VARCHAR(50) NOT NULL, -- salary, tax, utilities, insurance, subscription, other
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    frequency VARCHAR(20) DEFAULT 'monthly', -- daily, weekly, biweekly, monthly, quarterly, annually
    description TEXT,
    next_due_date DATE NOT NULL,
    is_recurring BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (company_id),
    INDEX (next_due_date)
);

-- ============================================================================
-- 2. FEATURE STORE (Behavioral Signals)
-- ============================================================================

-- Customer Payment Behavior Features
CREATE TABLE customer_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    
    -- Payment history metrics
    avg_days_to_pay DECIMAL(10, 2),
    median_days_to_pay DECIMAL(10, 2),
    payment_std_dev DECIMAL(10, 2),
    on_time_payment_rate DECIMAL(5, 2), -- 0-100
    late_payment_frequency INT, -- count of late payments
    
    -- Recent behavior (last 6 months)
    recent_avg_days_to_pay DECIMAL(10, 2),
    recent_payment_consistency_score DECIMAL(5, 2), -- 0-100
    
    -- Risk indicators
    overdue_invoice_count INT DEFAULT 0,
    total_overdue_amount DECIMAL(15, 2) DEFAULT 0,
    credit_risk_score DECIMAL(5, 2), -- 0-100 (higher = riskier)
    
    -- Transaction patterns
    invoice_count_last_3m INT,
    avg_invoice_amount DECIMAL(15, 2),
    
    -- Seasonal patterns
    high_payment_season VARCHAR(50),
    low_payment_season VARCHAR(50),
    
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (customer_id),
    INDEX (credit_risk_score)
);

-- Vendor Payment Behavior Features
CREATE TABLE vendor_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    vendor_id UUID NOT NULL,
    
    -- Delivery consistency
    avg_days_to_deliver DECIMAL(10, 2),
    delivery_consistency_score DECIMAL(5, 2), -- 0-100
    
    -- Payment terms compliance
    standard_terms INT, -- days
    avg_actual_payment_days DECIMAL(10, 2),
    early_payment_tendency BOOLEAN,
    
    -- Risk metrics
    supply_risk_score DECIMAL(5, 2), -- 0-100
    reliability_score DECIMAL(5, 2), -- 0-100
    
    -- Volume patterns
    po_count_last_3m INT,
    avg_po_amount DECIMAL(15, 2),
    
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (vendor_id),
    INDEX (supply_risk_score)
);

-- ============================================================================
-- 3. FORECAST & PREDICTIONS
-- ============================================================================

-- AR Collections Forecast
CREATE TABLE ar_collections_forecast (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    invoice_id UUID NOT NULL,
    
    predicted_payment_date DATE,
    confidence_score DECIMAL(5, 2), -- 0-100
    amount DECIMAL(15, 2),
    currency VARCHAR(3),
    
    -- Model details
    model_name VARCHAR(100),
    model_version VARCHAR(20),
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Explainability
    key_factors JSONB, -- {"factor": "weight", ...}
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (invoice_id),
    INDEX (predicted_payment_date)
);

-- Vendor Payment Forecast
CREATE TABLE vendor_payment_forecast (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    po_id UUID NOT NULL,
    
    predicted_payment_date DATE,
    confidence_score DECIMAL(5, 2),
    amount DECIMAL(15, 2),
    currency VARCHAR(3),
    
    payment_status VARCHAR(20), -- locked, flexible
    constraint_reason VARCHAR(100),
    
    model_name VARCHAR(100),
    model_version VARCHAR(20),
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    key_factors JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (po_id),
    INDEX (predicted_payment_date)
);

-- Project Billing Forecast
CREATE TABLE project_billing_forecast (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    milestone_id UUID NOT NULL,
    
    predicted_invoice_date DATE,
    predicted_payment_date DATE,
    confidence_score DECIMAL(5, 2),
    amount DECIMAL(15, 2),
    currency VARCHAR(3),
    
    completion_probability INT, -- 0-100
    
    model_name VARCHAR(100),
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    key_factors JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (milestone_id),
    INDEX (predicted_invoice_date)
);

-- Sales Pipeline Forecast
CREATE TABLE sales_pipeline_forecast (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    opportunity_id UUID NOT NULL,
    
    predicted_close_date DATE,
    predicted_invoice_date DATE,
    win_probability INT, -- 0-100
    confidence_score DECIMAL(5, 2),
    amount DECIMAL(15, 2),
    currency VARCHAR(3),
    
    model_name VARCHAR(100),
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    key_factors JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (opportunity_id),
    INDEX (predicted_invoice_date)
);

-- Other Inflows Forecast
CREATE TABLE other_inflows_forecast (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    inflow_id UUID NOT NULL,
    
    predicted_date DATE,
    confidence_score DECIMAL(5, 2),
    amount DECIMAL(15, 2),
    currency VARCHAR(3),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (inflow_id),
    INDEX (predicted_date)
);

-- Operational Expenses Forecast
CREATE TABLE opex_forecast (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    expense_id UUID NOT NULL,
    
    predicted_date DATE,
    confidence_score DECIMAL(5, 2),
    amount DECIMAL(15, 2),
    currency VARCHAR(3),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (expense_id),
    INDEX (predicted_date)
);

-- ============================================================================
-- 4. UNIFIED CASH FORECAST
-- ============================================================================

-- Normalized Cash Events (Single Source of Truth)
CREATE TABLE cash_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    
    event_date DATE NOT NULL,
    event_type VARCHAR(20) NOT NULL, -- inflow, outflow
    cash_category VARCHAR(50) NOT NULL, -- ar_collection, vendor_payment, project_billing, sales_pipeline, other_inflow, opex
    
    amount_original DECIMAL(15, 2),
    currency_original VARCHAR(3),
    amount_base DECIMAL(15, 2), -- converted to base currency
    base_currency VARCHAR(3),
    exchange_rate DECIMAL(10, 6),
    
    confidence_score DECIMAL(5, 2),
    source_id UUID, -- reference to original forecast record
    source_type VARCHAR(50),
    
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of UUID,
    
    forecast_accuracy DECIMAL(5, 2), -- filled after actual payment
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (company_id),
    INDEX (event_date),
    INDEX (event_type),
    INDEX (cash_category)
);

-- ============================================================================
-- 5. RECOMMENDATIONS
-- ============================================================================

CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    
    recommendation_type VARCHAR(50) NOT NULL, -- accelerate_ar, delay_vendor, adjust_budget, optimize_financing
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Impact analysis
    cash_impact_amount DECIMAL(15, 2),
    cash_impact_direction VARCHAR(20), -- increase, decrease
    
    -- Feasibility
    feasibility_score DECIMAL(5, 2), -- 0-100
    implementation_effort VARCHAR(20), -- low, medium, high
    implementation_timeframe VARCHAR(100),
    
    -- Priority
    priority_score DECIMAL(5, 2), -- 0-100 (higher = more important)
    ranking INT,
    
    -- Details
    affected_entities JSONB, -- list of customer/vendor/project IDs
    required_actions JSONB, -- action plan
    
    status VARCHAR(20) DEFAULT 'pending', -- pending, in_progress, completed, rejected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (company_id),
    INDEX (priority_score),
    INDEX (status)
);

-- ============================================================================
-- 6. MASTER DATA
-- ============================================================================

CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(255) NOT NULL,
    base_currency VARCHAR(3) DEFAULT 'USD',
    fiscal_year_start INT DEFAULT 1, -- 1 = January
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    customer_code VARCHAR(50),
    country VARCHAR(100),
    credit_limit DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (company_id)
);

CREATE TABLE vendors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    vendor_name VARCHAR(255) NOT NULL,
    vendor_code VARCHAR(50),
    country VARCHAR(100),
    payment_terms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (company_id)
);

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    project_name VARCHAR(255) NOT NULL,
    project_code VARCHAR(50),
    customer_id UUID NOT NULL,
    total_contract_value DECIMAL(15, 2),
    currency VARCHAR(3),
    start_date DATE,
    end_date DATE,
    status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (company_id),
    INDEX (customer_id)
);

-- ============================================================================
-- 7. AUDIT & ANALYTICS
-- ============================================================================

CREATE TABLE forecast_accuracy_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID NOT NULL,
    
    forecast_id UUID,
    forecast_type VARCHAR(50),
    predicted_date DATE,
    actual_date DATE,
    
    days_variance INT,
    accuracy_percentage DECIMAL(5, 2),
    
    amount_predicted DECIMAL(15, 2),
    amount_actual DECIMAL(15, 2),
    amount_variance DECIMAL(5, 2),
    
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (forecast_type),
    INDEX (logged_at)
);

CREATE TABLE model_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    model_name VARCHAR(100),
    model_version VARCHAR(20),
    model_type VARCHAR(50), -- ar_collections, vendor_payment, etc.
    
    mae DECIMAL(10, 6), -- Mean Absolute Error
    rmse DECIMAL(10, 6), -- Root Mean Squared Error
    r2_score DECIMAL(5, 2),
    
    training_samples INT,
    evaluation_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_invoices_company_customer ON invoices(company_id, customer_id);
CREATE INDEX idx_po_company_vendor ON purchase_orders(company_id, vendor_id);
CREATE INDEX idx_cash_events_date_range ON cash_events(company_id, event_date);
CREATE INDEX idx_ar_forecast_date ON ar_collections_forecast(company_id, predicted_payment_date);
CREATE INDEX idx_recommendations_priority ON recommendations(company_id, priority_score DESC, status);

-- ============================================================================
-- AUDIT TRIGGERS
-- ============================================================================

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_invoices_timestamp BEFORE UPDATE ON invoices
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_po_timestamp BEFORE UPDATE ON purchase_orders
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_cash_events_timestamp BEFORE UPDATE ON cash_events
FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ============================================================================
-- SAMPLE DATA (FOR TESTING)
-- ============================================================================

INSERT INTO companies (id, company_name, base_currency)
VALUES ('550e8400-e29b-41d4-a716-446655440000'::UUID, 'TechCorp Inc', 'USD');

INSERT INTO customers (id, company_id, customer_name, customer_code, country, credit_limit)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440001'::UUID, '550e8400-e29b-41d4-a716-446655440000'::UUID, 'Acme Corp', 'ACME', 'USA', 50000),
    ('550e8400-e29b-41d4-a716-446655440002'::UUID, '550e8400-e29b-41d4-a716-446655440000'::UUID, 'Global Solutions', 'GLOB', 'UK', 75000);

INSERT INTO vendors (id, company_id, vendor_name, vendor_code, country, payment_terms)
VALUES 
    ('550e8400-e29b-41d4-a716-446655440010'::UUID, '550e8400-e29b-41d4-a716-446655440000'::UUID, 'Supplier Inc', 'SUP1', 'USA', 30),
    ('550e8400-e29b-41d4-a716-446655440011'::UUID, '550e8400-e29b-41d4-a716-446655440000'::UUID, 'Material Co', 'MAT1', 'China', 45);