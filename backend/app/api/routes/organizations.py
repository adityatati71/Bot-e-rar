"""Organization and department routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import Organization, Department, User
from app.schemas.schemas import (
    OrganizationResponse, DepartmentResponse,
    OrganizationCreate, DepartmentCreate,
)
from app.security.auth import get_current_user

router = APIRouter()


@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all organizations."""
    orgs = db.query(Organization).filter(Organization.is_active == True).all()
    result = []
    for org in orgs:
        depts = db.query(Department).filter(
            Department.organization_id == org.id,
            Department.is_active == True,
        ).all()
        result.append(OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            logo_url=org.logo_url,
            is_active=org.is_active,
            departments=[DepartmentResponse.model_validate(d) for d in depts],
            created_at=org.created_at,
        ))
    return result


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get organization with departments."""
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    depts = db.query(Department).filter(
        Department.organization_id == org.id,
        Department.is_active == True,
    ).all()

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        logo_url=org.logo_url,
        is_active=org.is_active,
        departments=[DepartmentResponse.model_validate(d) for d in depts],
        created_at=org.created_at,
    )


@router.get("/{org_id}/departments", response_model=List[DepartmentResponse])
async def list_departments(
    org_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List departments for an organization."""
    depts = db.query(Department).filter(
        Department.organization_id == org_id,
        Department.is_active == True,
    ).all()
    return [DepartmentResponse.model_validate(d) for d in depts]


@router.post("", response_model=OrganizationResponse)
async def create_organization(
    request: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new organization."""
    import uuid
    org_id = f"org-{request.slug or uuid.uuid4().hex[:8]}"

    # Check for duplicate
    existing = db.query(Organization).filter(Organization.id == org_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Organization with slug '{request.slug}' already exists")

    org = Organization(
        id=org_id,
        name=request.name,
        slug=request.slug,
        description=request.description,
        is_active=True,
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    return OrganizationResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        description=org.description,
        logo_url=org.logo_url,
        is_active=org.is_active,
        departments=[],
        created_at=org.created_at,
    )


@router.post("/{org_id}/departments", response_model=DepartmentResponse)
async def create_department(
    org_id: str,
    request: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a department within an organization."""
    import uuid
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    slug = request.slug or "dept"
    existing = db.query(Department).filter(
        Department.organization_id == org_id,
        Department.slug == slug,
    ).first()
    if existing:
        return DepartmentResponse.model_validate(existing)

    dept_id = f"dept-{org_id}-{slug}-{uuid.uuid4().hex[:4]}"

    dept = Department(
        id=dept_id,
        organization_id=org_id,
        name=request.name,
        slug=slug,
        description=request.description,
        is_active=True,
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)

    return DepartmentResponse.model_validate(dept)

