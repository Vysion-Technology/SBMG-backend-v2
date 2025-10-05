from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database.survey import Form, Question, QuestionOption, Response, FormAssignment


class SurveyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_form(
        self,
        title: str,
        role_id: int,
        description: Optional[str],
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        created_by: int,
    ) -> Form:
        form = Form(
            title=title,
            role_id=role_id,
            description=description,
            start_date=start_date,
            end_date=end_date,
            created_by=created_by,
            created_at=datetime.now(tz=timezone.utc),
            active=True,
        )
        self.db.add(form)
        await self.db.commit()
        await self.db.refresh(form)
        return form

    async def get_form_by_id(self, form_id: int) -> Optional[Form]:
        result = await self.db.execute(select(Form).where(Form.id == form_id))
        return result.scalar_one_or_none()

    async def add_question(self, form_id: int, text: str, qtype: str, required: bool = True) -> Question:
        form = await self.get_form_by_id(form_id)
        if not form:
            raise ValueError("Form not found")
        question = Question(form_id=form_id, text=text, type=qtype, required=required)
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def get_question_by_id(self, question_id: int) -> Optional[Question]:
        result = await self.db.execute(select(Question).where(Question.id == question_id))
        return result.scalar_one_or_none()

    async def add_option(
        self,
        question_id: int,
        answer_type: str,
        text: str,
        description: Optional[str],
        created_by: int,
    ) -> QuestionOption:
        question = await self.get_question_by_id(question_id)
        if not question:
            raise ValueError("Question not found")
        option = QuestionOption(
            question_id=question_id,
            answer_type=answer_type,
            text=text,
            description=description,
            created_at=datetime.now(tz=timezone.utc),
            created_by=created_by,
        )
        self.db.add(option)
        await self.db.commit()
        await self.db.refresh(option)
        return option

    async def submit_responses(
        self, form_id: int, submitted_by: int, answers: List[dict[str, object]]
    ) -> List[Response]:
        # answers: list of {question_id: int, answer: str}
        form = await self.get_form_by_id(form_id)
        if not form:
            raise ValueError("Form not found")

        created = []
        for a in answers:
            qid = a.get("question_id")
            ans = a.get("answer")
            if qid is None or ans is None:
                continue
            resp = Response(
                form_id=form_id,
                question_id=qid,
                answer=str(ans),
                submitted_by=submitted_by,
                submitted_at=datetime.now(tz=timezone.utc),
            )
            self.db.add(resp)
            created.append(resp)

        await self.db.commit()
        # refresh created objects
        for r in created:
            await self.db.refresh(r)
        return created

    async def assign_form_to_users(self, form_id: int, assigned_by: int, user_ids: List[int]) -> List[FormAssignment]:
        form = await self.get_form_by_id(form_id)
        if not form:
            raise ValueError("Form not found")

        assignments = []
        for uid in user_ids:
            fa = FormAssignment(
                form_id=form_id,
                assigned_to=uid,
                assigned_by=assigned_by,
                assigned_at=datetime.now(tz=timezone.utc),
                completed=False,
            )
            # if user already has responses for this form, mark completed
            result = await self.db.execute(
                select(Response).where(Response.form_id == form_id, Response.submitted_by == uid)
            )
            existing = result.scalar_one_or_none()
            if existing:
                fa.completed = True
                fa.completed_at = existing.submitted_at
            self.db.add(fa)
            assignments.append(fa)

        await self.db.commit()
        for a in assignments:
            await self.db.refresh(a)
        return assignments

    async def get_available_forms_for_roles(self, roles: List[str]) -> List[Form]:
        if not roles:
            return []
        # role stored as string on Form
        query = select(Form).where(Form.active).where(Form.role.in_(roles))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_filled_forms_for_user(self, user_id: int) -> List[Form]:
        # get distinct form ids from responses
        result = await self.db.execute(select(Response.form_id).where(Response.submitted_by == user_id))
        form_ids = {r[0] for r in result.all()}
        if not form_ids:
            return []
        result2 = await self.db.execute(select(Form).where(Form.id.in_(list(form_ids))))
        return list(result2.scalars().all())

    async def get_assignments_for_user(self, user_id: int) -> List[FormAssignment]:
        result = await self.db.execute(select(FormAssignment).where(FormAssignment.assigned_to == user_id))
        return list(result.scalars().all())
