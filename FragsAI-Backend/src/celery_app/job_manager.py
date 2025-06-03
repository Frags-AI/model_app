from typing import List, Optional
from celery.result import AsyncResult
from celery_app.app import celery

class Job:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.status = 'queued'
        self.video_progress = 0
        self.motion_progress = 0
        self._result = AsyncResult(task_id, app=celery)

    def get_id(self) -> str:
        return self.task_id

    def get_status(self) -> str:
        return self._result.state or self.status

    def set_status(self, status: str):
        self.status = status

    def get_video_progress(self) -> int:
        info = self._result.info
        return info.get('clip_progress', self.video_progress)

    def set_video_progress(self, progress: int):
        self.video_progress = progress

    def get_frame_progress(self) -> int:
        info = self._result.info
        return info.get('motion_progress', self.motion_progress)

    def set_motion_progress(self, progress: int):
        self.motion_progress = progress

    def get_JSON(self) -> dict:
        return {
            'clip_progress': self.get_video_progress(),
            'motion_progress': self.get_frame_progress(),
        }

class JobManager:
    def __init__(self):
        self.jobs: List[Job] = []

    def is_empty(self) -> bool:
        return not self.jobs

    def exists(self, job_id: str) -> bool:
        return any(job.get_id() == job_id for job in self.jobs)

    def add_job(self, job_id: str) -> Job:
        job = Job(job_id)
        self.jobs.append(job)
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return next((job for job in self.jobs if job.get_id() == job_id), None)

    def remove_job(self, job_id: str) -> None:
        self.jobs = [job for job in self.jobs if job.get_id() != job_id]
        AsyncResult(job_id, app=celery).revoke(terminate=True)

    def get_job_status(self, job_id: str) -> Optional[str]:
        job = self.get_job(job_id)
        return job.get_status() if job else None

manager = JobManager()