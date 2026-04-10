"""
Feature Store Service

This module implements the central intelligence layer that calculates behavioral
features used by all forecasting models. It extracts signals from historical
transaction data and updates them periodically.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID
import logging

from models import (
    Invoice, PurchaseOrder, CustomerFeatures, VendorFeatures,
    Customer, Vendor
)
from schemas import CustomerFeaturesResponse, VendorFeaturesResponse
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class FeatureStore:
    """
    Central feature store for behavioral signals.
    
    Calculates features like:
    - Average days to pay
    - Payment consistency
    - Credit risk scores
    - Supply chain reliability
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.lookback_months = settings.FORECAST_LOOKBACK_MONTHS
        self.lookback_days = self.lookback_months * 30
        self.lookback_date = datetime.utcnow().date() - timedelta(days=self.lookback_days)
        self.lookback_3m_date = datetime.utcnow().date() - timedelta(days=90)
    
    # ========================================================================
    # CUSTOMER FEATURES (AR Collections)
    # ========================================================================
    
    def calculate_customer_features(self, company_id: UUID, customer_id: UUID) -> Optional[CustomerFeaturesResponse]:
        """
        Calculate comprehensive behavioral features for a customer.
        
        Features include:
        - Payment history metrics (avg days, std dev, consistency)
        - Recent payment behavior
        - Credit risk indicators
        - Transaction patterns
        """
        
        # Get all paid invoices for this customer (lookback period)
        paid_invoices = self.db.query(Invoice).filter(
            Invoice.company_id == company_id,
            Invoice.customer_id == customer_id,
            Invoice.status == 'paid',
            Invoice.payment_date >= self.lookback_date
        ).all()
        
        if not paid_invoices:
            logger.warning(f"No paid invoices found for customer {customer_id}")
            return None
        
        # Calculate days to pay for each invoice
        days_to_pay = []
        for invoice in paid_invoices:
            if invoice.payment_date and invoice.due_date:
                days = (invoice.payment_date - invoice.due_date).days
                days_to_pay.append(days)
        
        if not days_to_pay:
            return None
        
        # Basic statistics
        avg_days = Decimal(str(sum(days_to_pay) / len(days_to_pay)))
        median_days = Decimal(str(sorted(days_to_pay)[len(days_to_pay) // 2]))
        
        # Standard deviation
        variance = sum((x - float(avg_days)) ** 2 for x in days_to_pay) / len(days_to_pay)
        std_dev = Decimal(str(variance ** 0.5))
        
        # Recent behavior (last 3 months)
        recent_invoices = [inv for inv in paid_invoices if inv.payment_date >= self.lookback_3m_date]
        recent_days_to_pay = []
        for invoice in recent_invoices:
            if invoice.payment_date:
                days = (invoice.payment_date - invoice.due_date).days
                recent_days_to_pay.append(days)
        
        recent_avg_days = Decimal(str(sum(recent_days_to_pay) / len(recent_days_to_pay))) if recent_days_to_pay else avg_days
        
        # On-time payment rate
        on_time_count = sum(1 for days in days_to_pay if days <= 0)
        on_time_rate = Decimal(str((on_time_count / len(days_to_pay)) * 100))
        
        # Late payments
        late_count = sum(1 for days in days_to_pay if days > 0)
        
        # Consistency score (inverse of coefficient of variation)
        if avg_days != 0:
            cv = std_dev / avg_days
            consistency = Decimal(str(max(0, 100 - (cv * 100))))
        else:
            consistency = Decimal(100)
        
        # Overdue invoices
        overdue_invoices = self.db.query(Invoice).filter(
            Invoice.company_id == company_id,
            Invoice.customer_id == customer_id,
            Invoice.status == 'overdue'
        ).all()
        
        total_overdue = sum(Decimal(str(inv.amount)) for inv in overdue_invoices)
        
        # Credit risk score (0-100, higher = riskier)
        credit_risk = self._calculate_credit_risk_score(
            on_time_rate,
            consistency,
            overdue_invoices,
            total_overdue
        )
        
        # Invoice volume and amounts
        invoice_count_3m = len(recent_invoices) if recent_invoices else 0
        avg_invoice_amount = Decimal(str(sum(inv.amount for inv in paid_invoices) / len(paid_invoices)))
        
        # Store/update features
        existing_features = self.db.query(CustomerFeatures).filter(
            CustomerFeatures.company_id == company_id,
            CustomerFeatures.customer_id == customer_id
        ).first()
        
        if existing_features:
            existing_features.avg_days_to_pay = avg_days
            existing_features.median_days_to_pay = median_days
            existing_features.payment_std_dev = std_dev
            existing_features.on_time_payment_rate = on_time_rate
            existing_features.late_payment_frequency = late_count
            existing_features.recent_avg_days_to_pay = recent_avg_days
            existing_features.recent_payment_consistency_score = consistency
            existing_features.overdue_invoice_count = len(overdue_invoices)
            existing_features.total_overdue_amount = total_overdue
            existing_features.credit_risk_score = credit_risk
            existing_features.invoice_count_last_3m = invoice_count_3m
            existing_features.avg_invoice_amount = avg_invoice_amount
            existing_features.calculated_at = datetime.utcnow()
        else:
            features = CustomerFeatures(
                company_id=company_id,
                customer_id=customer_id,
                avg_days_to_pay=avg_days,
                median_days_to_pay=median_days,
                payment_std_dev=std_dev,
                on_time_payment_rate=on_time_rate,
                late_payment_frequency=late_count,
                recent_avg_days_to_pay=recent_avg_days,
                recent_payment_consistency_score=consistency,
                overdue_invoice_count=len(overdue_invoices),
                total_overdue_amount=total_overdue,
                credit_risk_score=credit_risk,
                invoice_count_last_3m=invoice_count_3m,
                avg_invoice_amount=avg_invoice_amount,
            )
            self.db.add(features)
        
        self.db.commit()
        
        return self._get_customer_features(company_id, customer_id)
    
    def _calculate_credit_risk_score(
        self,
        on_time_rate: Decimal,
        consistency: Decimal,
        overdue_invoices: list,
        total_overdue: Decimal
    ) -> Decimal:
        """
        Calculate credit risk score (0-100, higher = riskier)
        
        Factors:
        - On-time payment rate (weighted 40%)
        - Consistency (weighted 30%)
        - Overdue invoice count (weighted 20%)
        - Overdue amount (weighted 10%)
        """
        
        # On-time factor (0-100, lower on_time_rate = higher risk)
        on_time_factor = 100 - float(on_time_rate)
        
        # Consistency factor (0-100, lower consistency = higher risk)
        consistency_factor = 100 - float(consistency)
        
        # Overdue factors
        overdue_count_factor = min(100, len(overdue_invoices) * 10)
        overdue_amount_factor = min(100, float(total_overdue) / 1000) if total_overdue > 0 else 0
        
        # Weighted score
        risk_score = (
            (on_time_factor * 0.4) +
            (consistency_factor * 0.3) +
            (overdue_count_factor * 0.2) +
            (overdue_amount_factor * 0.1)
        )
        
        return Decimal(str(min(100, max(0, risk_score))))
    
    def _get_customer_features(
        self,
        company_id: UUID,
        customer_id: UUID
    ) -> Optional[CustomerFeaturesResponse]:
        """Retrieve customer features from database"""
        features = self.db.query(CustomerFeatures).filter(
            CustomerFeatures.company_id == company_id,
            CustomerFeatures.customer_id == customer_id
        ).first()
        
        return CustomerFeaturesResponse.from_orm(features) if features else None
    
    # ========================================================================
    # VENDOR FEATURES (Vendor Payments)
    # ========================================================================
    
    def calculate_vendor_features(self, company_id: UUID, vendor_id: UUID) -> Optional[VendorFeaturesResponse]:
        """
        Calculate comprehensive behavioral features for a vendor.
        
        Features include:
        - Delivery consistency
        - Payment terms compliance
        - Supply chain risk
        - Reliability scores
        """
        
        # Get all paid POs for this vendor
        paid_pos = self.db.query(PurchaseOrder).filter(
            PurchaseOrder.company_id == company_id,
            PurchaseOrder.vendor_id == vendor_id,
            PurchaseOrder.status == 'paid',
            PurchaseOrder.payment_date >= self.lookback_date
        ).all()
        
        if not paid_pos:
            logger.warning(f"No paid POs found for vendor {vendor_id}")
            return None
        
        # Calculate days to payment relative to scheduled date
        days_to_payment = []
        for po in paid_pos:
            if po.payment_date and po.scheduled_payment_date:
                days = (po.payment_date - po.scheduled_payment_date).days
                days_to_payment.append(days)
        
        if not days_to_payment:
            return None
        
        # Calculate metrics
        avg_payment_days = Decimal(str(sum(days_to_payment) / len(days_to_payment)))
        
        # Consistency score
        variance = sum((x - float(avg_payment_days)) ** 2 for x in days_to_payment) / len(days_to_payment)
        std_dev = variance ** 0.5
        
        if avg_payment_days != 0:
            cv = std_dev / float(avg_payment_days)
            consistency = Decimal(str(max(0, 100 - (cv * 100))))
        else:
            consistency = Decimal(100)
        
        # Early payment tendency
        early_payments = sum(1 for days in days_to_payment if days < 0)
        early_payment_tendency = early_payments > (len(days_to_payment) * 0.3)
        
        # Get vendor standard terms
        vendor = self.db.query(Vendor).filter(
            Vendor.id == vendor_id
        ).first()
        
        standard_terms = vendor.payment_terms if vendor else 30
        
        # Supply risk score (based on consistency and payment behavior)
        supply_risk = self._calculate_supply_risk_score(
            consistency,
            early_payment_tendency,
            len(paid_pos)
        )
        
        # Reliability score
        reliability = 100 - float(supply_risk)
        
        # Recent volume
        recent_pos = [po for po in paid_pos if po.payment_date >= self.lookback_3m_date]
        po_count_3m = len(recent_pos)
        avg_po_amount = Decimal(str(sum(po.amount for po in paid_pos) / len(paid_pos)))
        
        # Store/update features
        existing_features = self.db.query(VendorFeatures).filter(
            VendorFeatures.company_id == company_id,
            VendorFeatures.vendor_id == vendor_id
        ).first()
        
        if existing_features:
            existing_features.avg_days_to_deliver = Decimal(str(0))  # Placeholder
            existing_features.delivery_consistency_score = consistency
            existing_features.standard_terms = standard_terms
            existing_features.avg_actual_payment_days = avg_payment_days
            existing_features.early_payment_tendency = early_payment_tendency
            existing_features.supply_risk_score = supply_risk
            existing_features.reliability_score = Decimal(str(reliability))
            existing_features.po_count_last_3m = po_count_3m
            existing_features.avg_po_amount = avg_po_amount
            existing_features.calculated_at = datetime.utcnow()
        else:
            features = VendorFeatures(
                company_id=company_id,
                vendor_id=vendor_id,
                avg_days_to_deliver=Decimal(0),
                delivery_consistency_score=consistency,
                standard_terms=standard_terms,
                avg_actual_payment_days=avg_payment_days,
                early_payment_tendency=early_payment_tendency,
                supply_risk_score=supply_risk,
                reliability_score=Decimal(str(reliability)),
                po_count_last_3m=po_count_3m,
                avg_po_amount=avg_po_amount,
            )
            self.db.add(features)
        
        self.db.commit()
        
        return self._get_vendor_features(company_id, vendor_id)
    
    def _calculate_supply_risk_score(
        self,
        consistency: Decimal,
        early_payment_tendency: bool,
        po_count: int
    ) -> Decimal:
        """
        Calculate supply chain risk score (0-100, higher = riskier)
        
        Factors:
        - Consistency (40%)
        - Early payment risk (30%)
        - Transaction volume (30%)
        """
        
        # Consistency factor (lower consistency = higher risk)
        consistency_factor = 100 - float(consistency)
        
        # Early payment risk
        early_payment_factor = 30 if early_payment_tendency else 0
        
        # Volume factor (fewer transactions = higher risk)
        volume_factor = max(0, 30 - (po_count * 2))
        
        risk_score = (
            (consistency_factor * 0.4) +
            (early_payment_factor * 0.3) +
            (volume_factor * 0.3)
        )
        
        return Decimal(str(min(100, max(0, risk_score))))
    
    def _get_vendor_features(
        self,
        company_id: UUID,
        vendor_id: UUID
    ) -> Optional[VendorFeaturesResponse]:
        """Retrieve vendor features from database"""
        features = self.db.query(VendorFeatures).filter(
            VendorFeatures.company_id == company_id,
            VendorFeatures.vendor_id == vendor_id
        ).first()
        
        return VendorFeaturesResponse.from_orm(features) if features else None
    
    # ========================================================================
    # BATCH FEATURE CALCULATION
    # ========================================================================
    
    def calculate_all_customer_features(self, company_id: UUID) -> int:
        """
        Calculate features for all customers in a company.
        Used for batch feature updates.
        
        Returns: count of customers processed
        """
        customers = self.db.query(Customer).filter(
            Customer.company_id == company_id
        ).all()
        
        count = 0
        for customer in customers:
            try:
                self.calculate_customer_features(company_id, customer.id)
                count += 1
            except Exception as e:
                logger.error(f"Error calculating features for customer {customer.id}: {e}")
        
        logger.info(f"Calculated features for {count} customers in company {company_id}")
        return count
    
    def calculate_all_vendor_features(self, company_id: UUID) -> int:
        """
        Calculate features for all vendors in a company.
        
        Returns: count of vendors processed
        """
        vendors = self.db.query(Vendor).filter(
            Vendor.company_id == company_id
        ).all()
        
        count = 0
        for vendor in vendors:
            try:
                self.calculate_vendor_features(company_id, vendor.id)
                count += 1
            except Exception as e:
                logger.error(f"Error calculating features for vendor {vendor.id}: {e}")
        
        logger.info(f"Calculated features for {count} vendors in company {company_id}")
        return count
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_customer_features(
        self,
        company_id: UUID,
        customer_id: UUID
    ) -> Optional[CustomerFeaturesResponse]:
        """Get customer features, calculate if not exists"""
        features = self._get_customer_features(company_id, customer_id)
        
        if not features:
            features = self.calculate_customer_features(company_id, customer_id)
        
        return features
    
    def get_vendor_features(
        self,
        company_id: UUID,
        vendor_id: UUID
    ) -> Optional[VendorFeaturesResponse]:
        """Get vendor features, calculate if not exists"""
        features = self._get_vendor_features(company_id, vendor_id)
        
        if not features:
            features = self.calculate_vendor_features(company_id, vendor_id)
        
        return features