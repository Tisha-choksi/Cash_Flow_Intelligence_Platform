"""
Demo Data Loader

Loads sample financial data for development and testing purposes.
Creates realistic invoice, PO, and project data.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from decimal import Decimal
import random
import uuid

from models import (
    Company, Customer, Vendor, Invoice, PurchaseOrder,
    ProjectMilestone, Project, SalesOpportunity, OperationalExpense,
    OtherInflow
)


def load_demo_data(db: Session) -> int:
    """Load demo data into database. Returns count of records created."""
    
    record_count = 0
    
    # ========================================================================
    # Create Company
    # ========================================================================
    
    company = Company(
        company_name="TechCorp Inc",
        base_currency="USD",
        fiscal_year_start=1
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    company_id = company.id
    record_count += 1
    
    # ========================================================================
    # Create Customers
    # ========================================================================
    
    customers_data = [
        ("Acme Corp", "ACME", "USA", Decimal("50000")),
        ("Global Solutions", "GLOB", "UK", Decimal("75000")),
        ("Enterprise Systems", "ENT", "Canada", Decimal("100000")),
        ("Pacific Trading", "PAC", "Australia", Decimal("30000")),
        ("European Partners", "EUR", "Germany", Decimal("60000")),
    ]
    
    customers = []
    for cust_name, cust_code, country, credit_limit in customers_data:
        customer = Customer(
            company_id=company_id,
            customer_name=cust_name,
            customer_code=cust_code,
            country=country,
            credit_limit=credit_limit
        )
        db.add(customer)
        customers.append(customer)
        record_count += 1
    
    db.commit()
    
    # ========================================================================
    # Create Vendors
    # ========================================================================
    
    vendors_data = [
        ("Supplier Inc", "SUP1", "USA", 30),
        ("Material Co", "MAT1", "China", 45),
        ("Components Ltd", "COM1", "Japan", 60),
        ("Raw Materials Inc", "RAW1", "India", 30),
    ]
    
    vendors = []
    for vendor_name, vendor_code, country, payment_terms in vendors_data:
        vendor = Vendor(
            company_id=company_id,
            vendor_name=vendor_name,
            vendor_code=vendor_code,
            country=country,
            payment_terms=payment_terms
        )
        db.add(vendor)
        vendors.append(vendor)
        record_count += 1
    
    db.commit()
    
    # ========================================================================
    # Create Projects
    # ========================================================================
    
    projects = []
    for i, customer in enumerate(customers[:3]):
        project = Project(
            company_id=company_id,
            project_name=f"Project {i+1}: {customer.customer_name} Implementation",
            project_code=f"PROJ{i+1:03d}",
            customer_id=customer.id,
            total_contract_value=Decimal(str(random.randint(100000, 500000))),
            currency="USD",
            start_date=date.today() - timedelta(days=90),
            end_date=date.today() + timedelta(days=90),
            status="in_progress"
        )
        db.add(project)
        projects.append(project)
        record_count += 1
    
    db.commit()
    
    # ========================================================================
    # Create Sample Invoices (Past 6 months)
    # ========================================================================
    
    base_date = date.today()
    
    for customer in customers:
        for _ in range(random.randint(5, 15)):  # 5-15 invoices per customer
            days_back = random.randint(1, 180)  # Last 6 months
            issue_date = base_date - timedelta(days=days_back)
            due_date = issue_date + timedelta(days=30)
            
            invoice_status = "paid"
            payment_date = None
            paid_amount = None
            
            # 85% of invoices are paid
            if random.random() < 0.85:
                invoice_status = "paid"
                # 70% paid on time, 30% late
                if random.random() < 0.7:
                    payment_date = due_date + timedelta(days=random.randint(0, 10))
                else:
                    payment_date = due_date + timedelta(days=random.randint(11, 60))
                paid_amount = Decimal(str(random.randint(10000, 100000)))
            
            elif random.random() < 0.1:
                invoice_status = "overdue"
                payment_date = None
                paid_amount = Decimal(0)
            
            else:
                invoice_status = "unpaid"
                payment_date = None
                paid_amount = Decimal(0)
            
            invoice = Invoice(
                company_id=company_id,
                customer_id=customer.id,
                invoice_number=f"INV-{customer.customer_code}-{uuid.uuid4().hex[:8].upper()}",
                amount=Decimal(str(random.randint(10000, 100000))),
                currency="USD",
                issue_date=issue_date,
                due_date=due_date,
                status=invoice_status,
                payment_date=payment_date,
                paid_amount=paid_amount if paid_amount else Decimal(0)
            )
            db.add(invoice)
            record_count += 1
    
    db.commit()
    
    # ========================================================================
    # Create Sample Purchase Orders (Past 6 months)
    # ========================================================================
    
    for vendor in vendors:
        for _ in range(random.randint(8, 20)):  # 8-20 POs per vendor
            days_back = random.randint(1, 180)
            order_date = base_date - timedelta(days=days_back)
            scheduled_payment_date = order_date + timedelta(days=vendor.payment_terms or 30)
            
            po_status = "paid"
            payment_date = None
            paid_amount = None
            
            # 75% of POs are paid
            if random.random() < 0.75:
                po_status = "paid"
                # 80% paid by scheduled date or early, 20% late
                if random.random() < 0.8:
                    payment_date = scheduled_payment_date + timedelta(days=random.randint(-5, 3))
                else:
                    payment_date = scheduled_payment_date + timedelta(days=random.randint(4, 30))
                paid_amount = Decimal(str(random.randint(5000, 50000)))
            
            else:
                po_status = "pending"
                payment_date = None
                paid_amount = Decimal(0)
            
            po = PurchaseOrder(
                company_id=company_id,
                vendor_id=vendor.id,
                po_number=f"PO-{vendor.vendor_code}-{uuid.uuid4().hex[:8].upper()}",
                amount=Decimal(str(random.randint(5000, 50000))),
                currency="USD",
                order_date=order_date,
                scheduled_payment_date=scheduled_payment_date,
                status=po_status,
                payment_date=payment_date,
                paid_amount=paid_amount if paid_amount else Decimal(0),
                vendor_payment_terms=vendor.payment_terms
            )
            db.add(po)
            record_count += 1
    
    db.commit()
    
    # ========================================================================
    # Create Project Milestones
    # ========================================================================
    
    for project in projects:
        milestone_count = random.randint(3, 5)
        total_amount = project.total_contract_value
        milestone_amount = total_amount / milestone_count
        
        for i in range(milestone_count):
            milestone = ProjectMilestone(
                company_id=company_id,
                project_id=project.id,
                customer_id=project.customer_id,
                milestone_name=f"{project.project_name} - Phase {i+1}",
                contract_amount=total_amount,
                milestone_amount=milestone_amount,
                currency="USD",
                scheduled_completion=project.start_date + timedelta(days=30 * (i + 1)),
                status=random.choice(["pending", "in_progress", "completed"]),
                completion_percentage=random.choice([0, 25, 50, 75, 100])
            )
            db.add(milestone)
            record_count += 1
    
    db.commit()
    
    # ========================================================================
    # Create Sales Opportunities
    # ========================================================================
    
    stages = ["prospecting", "negotiation", "proposal", "decision"]
    
    for customer in customers:
        for _ in range(random.randint(1, 3)):
            opportunity = SalesOpportunity(
                company_id=company_id,
                customer_id=customer.id,
                opportunity_name=f"Opportunity for {customer.customer_name}",
                opportunity_amount=Decimal(str(random.randint(50000, 500000))),
                currency="USD",
                stage=random.choice(stages),
                probability=random.randint(10, 90),
                expected_close_date=date.today() + timedelta(days=random.randint(1, 120))
            )
            db.add(opportunity)
            record_count += 1
    
    db.commit()
    
    # ========================================================================
    # Create Operational Expenses
    # ========================================================================
    
    expenses = [
        ("salary", "monthly", Decimal("150000")),
        ("utilities", "monthly", Decimal("5000")),
        ("insurance", "quarterly", Decimal("25000")),
        ("taxes", "quarterly", Decimal("50000")),
        ("software_licenses", "monthly", Decimal("10000")),
    ]
    
    for expense_type, frequency, amount in expenses:
        expense = OperationalExpense(
            company_id=company_id,
            expense_type=expense_type,
            amount=amount,
            currency="USD",
            frequency=frequency,
            next_due_date=date.today() + timedelta(days=30),
            is_recurring=True
        )
        db.add(expense)
        record_count += 1
    
    db.commit()
    
    # ========================================================================
    # Create Other Inflows
    # ========================================================================
    
    inflow = OtherInflow(
        company_id=company_id,
        inflow_type="loan",
        amount=Decimal("500000"),
        currency="USD",
        description="Business line of credit",
        expected_date=date.today() + timedelta(days=15),
        status="approved"
    )
    db.add(inflow)
    record_count += 1
    
    db.commit()
    
    print(f"\n✅ Demo data loaded successfully!")
    print(f"📊 Created {record_count} records in database")
    print(f"🏢 Company: {company.company_name}")
    print(f"👥 Customers: {len(customers)}")
    print(f"🏭 Vendors: {len(vendors)}")
    print(f"📋 Projects: {len(projects)}")
    
    return record_count