"""
Company Management API Routes

Routes for managing company/tenant data in the system.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models import Company
from app.schemas import CompanyCreate, CompanyResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/companies", tags=["Master Data"])


@router.post("", response_model=CompanyResponse)
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


@router.get("/{company_id}", response_model=CompanyResponse)
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


@router.get("", response_model=list[CompanyResponse])
async def list_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all companies with pagination.
    """
    try:
        companies = db.query(Company).offset(skip).limit(limit).all()
        return companies
    
    except Exception as e:
        logger.error(f"Error listing companies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing companies: {str(e)}"
        )