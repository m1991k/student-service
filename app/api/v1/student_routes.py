from fastapi import APIRouter, HTTPException
from app.models.student import Student
from app.repositories.student_repository import StudentRepository
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/")
async def create_student(student: Student):
    logger.info(f"Creating student: {student}")
    try:
        sid = await StudentRepository.create(student.model_dump(exclude={"id"}))
        logger.info(f"Student created with ID: {sid}")
        return {"id": sid}
    except Exception as e:
        logger.error(f"Error creating student: {e}", exc_info=True)
        raise HTTPException(500, f"Error creating student: {str(e)}")

@router.get("/")
async def get_students():
    logger.info("Fetching all students")
    try:
        students = await StudentRepository.get_all()
        logger.info(f"Found {len(students)} students")
        return students
    except Exception as e:
        logger.error(f"Error fetching students: {e}", exc_info=True)
        raise HTTPException(500, f"Error fetching students: {str(e)}")

@router.get("/{student_id}")
async def get_student(student_id: str):
    logger.info(f"Fetching student with ID: {student_id}")
    try:
        student = await StudentRepository.get_by_id(student_id)
        if not student:
            logger.warning(f"Student not found: {student_id}")
            raise HTTPException(404, "Student not found")
        return student
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student {student_id}: {e}", exc_info=True)
        raise HTTPException(500, f"Error fetching student: {str(e)}")

@router.put("/{student_id}")
async def update_student(student_id: str, student: Student):
    logger.info(f"Updating student with ID: {student_id}")
    try:
        await StudentRepository.update(student_id, student.model_dump(exclude={"id"}))
        logger.info(f"Student {student_id} updated")
        return {"message": "updated"}
    except Exception as e:
        logger.error(f"Error updating student {student_id}: {e}", exc_info=True)
        raise HTTPException(500, f"Error updating student: {str(e)}")

@router.delete("/{student_id}")
async def delete_student(student_id: str):
    logger.info(f"Deleting student with ID: {student_id}")
    try:
        await StudentRepository.delete(student_id)
        logger.info(f"Student {student_id} deleted")
        return {"message": "deleted"}
    except Exception as e:
        logger.error(f"Error deleting student {student_id}: {e}", exc_info=True)
        raise HTTPException(500, f"Error deleting student: {str(e)}")
