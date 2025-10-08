from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.survey import SurveyService
from controllers.auth import get_current_active_user
from auth_utils import require_admin
from models.database.auth import User
from models.response.survey import FormResponse, FilledFormResponse, AssignmentResponse


router = APIRouter()


class CreateFormRequest(BaseModel):
    title: str
    role_id: int
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class UpdateFormRequest(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class AddQuestionRequest(BaseModel):
    text: str
    type: str
    required: bool = True


class AddOptionRequest(BaseModel):
    answer_type: str
    text: str
    description: Optional[str] = None


class SubmitAnswersRequest(BaseModel):
    answers: List[dict[str, object]]


@router.post("/forms", status_code=201)
async def create_form(
    req: CreateFormRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    svc = SurveyService(db)
    try:
        form = await svc.create_form(
            title=req.title,
            role_id=req.role_id,
            description=req.description,
            start_date=req.start_date,
            end_date=req.end_date,
            created_by=current_user.id,
        )
        return {"id": form.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/forms/{form_id}", status_code=200)
async def update_form(
    form_id: int,
    req: UpdateFormRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    svc = SurveyService(db)
    form = await svc.get_form_by_id(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    if form.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only creator can update this form")
    try:
        form.title = req.title
        form.description = req.description  # type: ignore
        form.start_date = req.start_date  # type: ignore
        form.end_date = req.end_date  # type: ignore
        await db.commit()
        return {"id": form.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/forms/{form_id}/questions", status_code=201)
async def add_question(
    form_id: int,
    req: AddQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    svc = SurveyService(db)
    try:
        q = await svc.add_question(form_id, req.text, req.type, req.required)
        return {"id": q.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/questions/{question_id}/options", status_code=201)
async def add_option(
    question_id: int,
    req: AddOptionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    svc = SurveyService(db)
    try:
        opt = await svc.add_option(
            question_id, req.answer_type, req.text, req.description, current_user.id
        )
        return {"id": opt.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/forms/{form_id}/submit", status_code=201)
async def submit_form(
    form_id: int,
    req: SubmitAnswersRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = SurveyService(db)
    # Only users whose role matches form.role should be allowed, unless admin
    form = await svc.get_form_by_id(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    # get user roles
    user_roles = [pos.role.name for pos in current_user.positions if pos.role]
    if form.role not in user_roles and "ADMIN" not in user_roles:
        raise HTTPException(
            status_code=403, detail="User not authorized to submit this form"
        )

    try:
        created = await svc.submit_responses(form_id, current_user.id, req.answers)
        return {"created": len(created)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/forms/{form_id}/assign", status_code=201)
async def assign_form(
    form_id: int,
    user_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Only creator of form can assign (or admin)
    svc = SurveyService(db)
    form = await svc.get_form_by_id(form_id)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")

    user_roles = [pos.role.name for pos in current_user.positions if pos.role]
    if form.created_by != current_user.id and "ADMIN" not in user_roles:
        raise HTTPException(
            status_code=403, detail="Only creator or admin can assign this form"
        )

    try:
        assignments = await svc.assign_form_to_users(form_id, current_user.id, user_ids)
        return {"assigned": len(assignments)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))




@router.get("/forms/available")
async def available_forms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[FormResponse]:
    svc = SurveyService(db)
    user_roles = [pos.role.name for pos in current_user.positions if pos.role]
    forms = await svc.get_available_forms_for_roles(user_roles)
    return [FormResponse(id=f.id, title=f.title, role=f.role.name) for f in forms]



@router.get("/forms/filled")
async def filled_forms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[FilledFormResponse]:
    svc = SurveyService(db)
    forms = await svc.get_filled_forms_for_user(current_user.id)
    return [FilledFormResponse(id=f.id, title=f.title) for f in forms]





@router.get("/forms/assignments")
async def assignments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = SurveyService(db)
    assigns = await svc.get_assignments_for_user(current_user.id)
    return [
        AssignmentResponse(
            id=a.id, form_id=a.form_id, assigned_at=a.assigned_at, completed=a.completed
        )
        for a in assigns
    ]
