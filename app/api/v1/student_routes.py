from fastapi import APIRouter, HTTPException
from app.models.student import Student
from app.repositories.student_repository import StudentRepository

router = APIRouter()

@router.post("/")
async def create_student(student: Student):
    sid = await StudentRepository.create(student.model_dump(exclude={"id"}))
    return {"id": sid}

@router.get("/")
async def get_students():
    return await StudentRepository.get_all()

@router.get("/{student_id}")
async def get_student(student_id: str):
    student = await StudentRepository.get_by_id(student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    return student

@router.put("/{student_id}")
async def update_student(student_id: str, student: Student):
    await StudentRepository.update(student_id, student.model_dump(exclude={"id"}))
    return {"message": "updated"}

@router.delete("/{student_id}")
async def delete_student(student_id: str):
    await StudentRepository.delete(student_id)
    return {"message": "deleted"}
