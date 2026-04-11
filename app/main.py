"""
Cash Flow Intelligence Platform - FastAPI Backend

Main application entry point with middleware setup, dependency injection,
and basic API endpoints.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import logging

from config import get_settings
from database import SessionLocal, init_db, engine, Base, get_db
from app.models import Company
from schemas import (
    HealthCheckResponse,
    CompanyCreate,
    CompanyResponse,
    DashboardMetrics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# ============================================================================
# INITIALIZE DATABASE TABLES
# ============================================================================

try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {e}")

# ============================================================================
# CREATE FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="ML-driven cash flow forecasting and decision intelligence platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# ============================================================================
# MIDDLEWARE SETUP
# ============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/api/health", response_model=HealthCheckResponse, tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify API and database connectivity.
    """
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        db_status = False
    
    status_msg = "healthy" if db_status else "degraded"
    message = "All systems operational" if db_status else "Database connection failed"
    
    if not db_status:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "message": "Database connection failed",
                "database_connected": False,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return HealthCheckResponse(
        status=status_msg,
        message=message,
        database_connected=db_status,
        timestamp=datetime.utcnow()
    )


# ============================================================================
# COMPANY MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/companies", response_model=CompanyResponse, tags=["Master Data"])
async def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    """
    Create a new company/tenant in the system.
    """
    try:
        db_company = Company(
            company_name=company.company_name,
            base_currency=company.base_currency,
            fiscal_year_start=company.fiscal_year_start
        )
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        
        logger.info(f"Company created: {db_company.id}")
        return db_company
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating company: {str(e)}"
        )


@app.get("/api/companies/{company_id}", response_model=CompanyResponse, tags=["Master Data"])
async def get_company(company_id: str, db: Session = Depends(get_db)):
    """
    Get company details by ID.
    """
    try:
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company {company_id} not found"
            )
        
        return company
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving company: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving company: {str(e)}"
        )


# ============================================================================
# INITIALIZATION ENDPOINT (For Demo/Testing)
# ============================================================================

@app.post("/api/system/init-demo-data", tags=["System"])
async def init_demo_data(db: Session = Depends(get_db)):
    """
    Initialize demo data for testing purposes.
    WARNING: Only use in development environments!
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo data initialization only available in debug mode"
        )
    
    try:
        from demo_data import load_demo_data
        count = load_demo_data(db)
        
        return {
            "status": "success",
            "message": f"Demo data loaded successfully",
            "records_created": count
        }
    
    except Exception as e:
        logger.error(f"Error loading demo data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error loading demo data: {str(e)}"
        )


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["System"])
async def root():
    """
    API root endpoint with documentation links.
    """
    return {
        "message": "Cash Flow Intelligence Platform API",
        "version": settings.API_VERSION,
        "documentation": "/api/docs",
        "openapi": "/api/openapi.json",
        "health": "/api/health"
    }


# ============================================================================
# API ENDPOINT STUBS (To be implemented in subsequent phases)
# ============================================================================

# Forecast Endpoints (Phase 2)
@app.post("/api/forecasts/ar-collections", tags=["Forecasts (Phase 2)"])
async def create_ar_forecast():
    """Create AR collection forecast - Coming in Phase 2"""
    return {"message": "AR Collections forecast endpoint - Phase 2"}

@app.post("/api/forecasts/vendor-payments", tags=["Forecasts (Phase 2)"])
async def create_vendor_forecast():
    """Create vendor payment forecast - Coming in Phase 2"""
    return {"message": "Vendor Payment forecast endpoint - Phase 2"}

@app.get("/api/forecasts/unified-cash-position/{company_id}", tags=["Forecasts (Phase 2)"])
async def get_unified_forecast():
    """Get unified cash forecast - Coming in Phase 2"""
    return {"message": "Unified cash forecast endpoint - Phase 2"}

# Recommendations Endpoint (Phase 3)
@app.get("/api/recommendations/{company_id}", tags=["Recommendations (Phase 3)"])
async def get_recommendations():
    """Get intelligent recommendations - Coming in Phase 3"""
    return {"message": "Recommendations endpoint - Phase 3"}

# Dashboard Endpoint (Phase 4)
@app.get("/api/dashboard/{company_id}", tags=["Dashboard (Phase 4)"])
async def get_dashboard():
    """Get dashboard metrics - Coming in Phase 4"""
    return {"message": "Dashboard endpoint - Phase 4"}


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "status": "error"
        }
    )


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Cash Flow Intelligence Platform API starting up...")
    logger.info(f"API Version: {settings.API_VERSION}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info(f"Database URL: {settings.DATABASE_URL}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Cash Flow Intelligence Platform API shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )