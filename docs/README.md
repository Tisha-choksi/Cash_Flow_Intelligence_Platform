# Cash Flow Intelligence Platform - Backend

**ML-driven cash flow forecasting and decision intelligence system** built with FastAPI, PostgreSQL, and Python ML libraries.

---

## 📋 Project Overview

This platform predicts cash inflows and outflows, combines them into a unified forecast, and recommends actions to optimize liquidity. It's designed as a **decision-support system for treasury teams**.

### Core Components

```
Raw Financial Data (Invoices, POs, Projects, Sales, Expenses)
        ↓
Feature Store (Behavioral Signals - centralized intelligence)
        ↓
6 Forecasting Engines (AR, Vendor, Project, Sales, Other Inflows, OpEx)
        ↓
Cash Event Normalization (Dedupe, Currency Convert, Confidence Score)
        ↓
Unified Cash Forecast (Single source of truth)
        ↓
Recommendation Engine (Actionable intelligence)
        ↓
Treasury Decision Layer (API for frontend consumption)
```

---

## 🏗️ Architecture

### Tech Stack

- **Backend Framework**: FastAPI (async, modern Python)
- **Database**: PostgreSQL (relational, complex financial data)
- **ORM**: SQLAlchemy 2.0 (type-safe, efficient)
- **ML Libraries**: XGBoost, LightGBM, scikit-learn
- **Async**: asyncio with uvicorn
- **Data Processing**: Pandas, NumPy

### Project Structure

```
.
├── main.py                 # FastAPI app entry point
├── config.py              # Configuration management
├── database.py            # DB connection & session
├── models.py              # SQLAlchemy ORM models
├── schemas.py             # Pydantic validation schemas
├── feature_store.py       # Central intelligence layer
├── demo_data.py           # Sample data loader
├── requirements.txt       # Dependencies
├── schema.sql            # PostgreSQL DDL
└── README.md             # This file
```

### Core Modules (Phase 2-3 Implementation)

**Phase 1 (Complete)**: Database schema + Feature Store + API foundation

**Phase 2 (Next)**: 6 Forecasting Engines
- `ar_collections.py` - Customer payment prediction (XGBoost)
- `vendor_payments.py` - Vendor payment forecast (Hybrid rule-based + ML)
- `project_billing.py` - Milestone-based revenue forecast
- `sales_pipeline.py` - Deal probability + timing
- `other_inflows.py` - Loans, grants, refunds
- `operational_expenses.py` - Recurring costs

**Phase 3 (Later)**: Recommendation Engine
- `cash_event_normalizer.py` - Merge forecasts, dedupe, currency convert
- `recommendation_engine.py` - Suggest AR acceleration, vendor delays, etc.

**Phase 4 (Final)**: Analytics & Dashboard API
- Analytics endpoints
- Forecast accuracy tracking
- Model performance monitoring

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 13+
- pip/conda

### Installation

1. **Clone or extract the project**
   ```bash
   cd cashflow-intelligence
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup PostgreSQL**
   ```bash
   # Create database
   createdb cashflow_db
   
   # Optional: Load schema manually
   psql cashflow_db < schema.sql
   ```

5. **Configure environment**
   ```bash
   # Create .env file
   cat > .env << EOF
   DATABASE_URL=postgresql://postgres:postgres@localhost:5432/cashflow_db
   DEBUG=True
   SECRET_KEY=dev-key-change-in-production
   FORECAST_HORIZON_DAYS=90
   FORECAST_LOOKBACK_MONTHS=6
   EOF
   ```

6. **Run the server**
   ```bash
   python main.py
   
   # Or with uvicorn
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Load demo data**
   ```bash
   # Once server is running, call:
   curl -X POST http://localhost:8000/api/system/init-demo-data
   ```

---

## 📚 API Documentation

### Health & System

- `GET /api/health` - System status
- `POST /api/system/init-demo-data` - Load test data

### Master Data Management

- `POST /api/companies` - Create company
- `GET /api/companies/{company_id}` - Get company details

### Forecasting (Phase 2)

- `POST /api/forecasts/ar-collections` - Create AR forecast
- `POST /api/forecasts/vendor-payments` - Create vendor forecast
- `GET /api/forecasts/unified-cash-position/{company_id}` - Unified forecast

### Recommendations (Phase 3)

- `GET /api/recommendations/{company_id}` - Get recommendations
- `PUT /api/recommendations/{recommendation_id}` - Update recommendation status

### Dashboard (Phase 4)

- `GET /api/dashboard/{company_id}` - Dashboard metrics

---

## 🧠 Feature Store (Core Intelligence)

The **Feature Store** (`feature_store.py`) is the system's brain. It:

1. **Calculates behavioral features** from historical data
2. **Stores features** for reuse by all models
3. **Updates periodically** via batch jobs

### Customer Features

```python
{
    "avg_days_to_pay": 25,
    "median_days_to_pay": 24,
    "payment_std_dev": 8.5,
    "on_time_payment_rate": 72,  # %
    "late_payment_frequency": 3,
    "credit_risk_score": 28,  # 0-100, higher = riskier
    "overdue_invoice_count": 1,
    "total_overdue_amount": 15000
}
```

### Vendor Features

```python
{
    "avg_days_to_deliver": 14,
    "delivery_consistency_score": 85,
    "avg_actual_payment_days": 32,
    "early_payment_tendency": false,
    "supply_risk_score": 15,  # 0-100, lower = safer
    "reliability_score": 85,
    "po_count_last_3m": 12,
    "avg_po_amount": 25000
}
```

### Usage

```python
from database import SessionLocal
from feature_store import FeatureStore

db = SessionLocal()
fs = FeatureStore(db)

# Calculate for single customer
features = fs.calculate_customer_features(company_id, customer_id)

# Or retrieve if exists
features = fs.get_customer_features(company_id, customer_id)

# Batch calculation
fs.calculate_all_customer_features(company_id)
fs.calculate_all_vendor_features(company_id)
```

---

## 📊 Database Schema Highlights

### Core Financial Tables

- **invoices** - AR source (3000+ records expected)
- **purchase_orders** - Vendor payments (2000+)
- **project_milestones** - Project-based billing
- **sales_opportunities** - Pipeline forecasting
- **operational_expenses** - Recurring costs
- **other_inflows** - Loans, grants, etc.

### Feature Tables

- **customer_features** - Behavioral signals (updated daily)
- **vendor_features** - Supply/payment behavior

### Forecast Tables

- **ar_collections_forecast** - Payment predictions
- **vendor_payment_forecast** - Vendor payment timing
- **project_billing_forecast** - Milestone revenue timing
- **sales_pipeline_forecast** - Deal closure + cash timing

### Unified Forecast

- **cash_events** - Normalized, deduplicated events (single source of truth)

### Recommendations

- **recommendations** - Actionable suggestions ranked by priority

---

## 🤖 Model Architecture (Phase 2 Preview)

### AR Collections (S1)

**Model**: XGBoost Regressor
**Input Features**: Customer features + invoice-specific data
**Output**: Predicted payment date + confidence score
**Update Mechanism**: Event-driven (on new invoice)

```python
# Features:
- avg_days_to_pay
- payment_std_dev
- credit_risk_score
- invoice_amount (relative to average)
- days_past_due_date
- customer_industry
- seasonality_factor
```

### Vendor Payments (S2)

**Model**: Hybrid (Rule-based + LightGBM)
**Rules**: Payment terms + vendor features
**ML Adjustment**: Predict deviations from terms
**Output**: Predicted payment date + flexibility flag

```python
# Rule-based: scheduled_payment = order_date + vendor_terms
# ML adjusts: ±days based on vendor behavior
# Liquidity gating: Delays if cash < threshold
```

### Project Billing (S3)

**Model**: Rule-based milestone tracking (Future: Probabilistic)
**Logic**: Based on % completion + milestone dates
**Output**: Predicted invoice date + confidence

### Sales Pipeline (S4)

**Model**: LightGBM (stage-specific)
**Input**: Deal stage, days in stage, deal size, rep history
**Output**: Win probability + predicted close date
**Stop Condition**: Once invoice is generated

### Other Inflows (S5) & OpEx (S6)

**Model**: Simple scheduling
**Logic**: Historical pattern matching + explicit dates

---

## 📈 Performance & Monitoring

### Forecast Accuracy Tracking

```python
# Logged in forecast_accuracy_log table
{
    "forecast_type": "ar_collections",
    "predicted_date": "2025-04-15",
    "actual_date": "2025-04-18",
    "days_variance": 3,
    "accuracy_percentage": 95,
    "amount_predicted": 50000,
    "amount_actual": 49500
}
```

### Model Performance Metrics

```python
# In model_performance table
{
    "model_name": "ar_xgboost",
    "model_version": "1.0",
    "mae": 4.2,  # days
    "rmse": 5.8,
    "r2_score": 0.87,
    "training_samples": 5000,
    "evaluation_date": "2025-01-15"
}
```

### Retraining Strategy

- Batch retraining: Weekly
- Trigger: When accuracy drops below threshold
- Feedback loop: Actual vs. predicted → retrain

---

## 🔐 Security (Production)

- [ ] API authentication (JWT)
- [ ] Rate limiting
- [ ] Input validation (Pydantic)
- [ ] SQL injection prevention (SQLAlchemy)
- [ ] Secrets management (.env, AWS Secrets)
- [ ] HTTPS enforcement
- [ ] CORS configuration
- [ ] Audit logging
- [ ] Data encryption at rest

---

## 🛠️ Development Workflow

### Adding a New Forecasting Module

1. **Create model** in `forecasts/{module_name}.py`
2. **Create ORM model** in `models.py`
3. **Create schema** in `schemas.py`
4. **Add API endpoint** in `main.py`
5. **Write tests** in `tests/test_{module_name}.py`
6. **Update documentation**

### Example: Adding AR Collections Forecast

```python
# forecasts/ar_collections.py
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
from feature_store import FeatureStore

class ARCollectionsForecaster:
    def __init__(self, model_path=None):
        self.model = XGBRegressor(n_estimators=100)
        self.scaler = StandardScaler()
    
    def predict(self, invoice, customer_features):
        # Extract features
        features = self._extract_features(invoice, customer_features)
        
        # Normalize
        features_scaled = self.scaler.transform([features])
        
        # Predict days to payment
        days_to_payment = self.model.predict(features_scaled)[0]
        
        # Convert to payment date
        payment_date = invoice.due_date + timedelta(days=int(days_to_payment))
        
        # Calculate confidence
        confidence = self._calculate_confidence(days_to_payment, customer_features)
        
        return payment_date, confidence
```

---

## 📝 Sample Usage Workflow

```python
# 1. Initialize
from database import SessionLocal
from feature_store import FeatureStore
from models import Company, Customer, Invoice

db = SessionLocal()
company_id = "550e8400-e29b-41d4-a716-446655440000"

# 2. Calculate features for all customers
fs = FeatureStore(db)
fs.calculate_all_customer_features(company_id)

# 3. Run AR forecast (Phase 2)
# from forecasts.ar_collections import ARCollectionsForecaster
# forecaster = ARCollectionsForecaster()
# for invoice in invoices:
#     payment_date, confidence = forecaster.predict(invoice, features)

# 4. Normalize cash events (Phase 3)
# events = normalize_cash_events([ar_forecasts, vendor_forecasts, ...])

# 5. Generate recommendations (Phase 3)
# recommendations = generate_recommendations(unified_forecast)

# 6. Return via API (Phase 4)
# GET /api/recommendations/{company_id}
```

---

## 🧪 Testing

```bash
# Run tests (not yet implemented)
pytest tests/ -v

# Test coverage
pytest --cov=.

# Test specific module
pytest tests/test_feature_store.py -v
```

---

## 📞 Support & Questions

For questions or issues:
1. Check the API docs: `http://localhost:8000/api/docs`
2. Review the models: `models.py`
3. Review the feature store: `feature_store.py`

---

## 📅 Phase Timeline

- **Phase 1** ✅ Complete: DB schema + Feature Store + API foundation
- **Phase 2** 🔄 In Progress: 6 Forecasting engines
- **Phase 3** ⏳ Coming: Cash normalization + Recommendations
- **Phase 4** ⏳ Coming: Dashboard + Analytics

---

## 🎯 Key Design Principles

1. **Feature Reuse**: All models use same feature store (DRY, consistency)
2. **Event-Driven**: Forecasts update on data changes
3. **Confidence Scores**: Every prediction includes confidence (0-100)
4. **Explainability**: Key factors driving each prediction
5. **Modularity**: Each forecasting engine is independent
6. **Normalization**: Single cash event source of truth
7. **Testability**: Mock data, batch operations, feedback loops

---

**Built with ❤️ for treasury teams | Last updated: April 2025**