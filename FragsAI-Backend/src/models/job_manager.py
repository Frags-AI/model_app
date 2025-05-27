from typing import List

class Job():
    def __init__(self, id: str):
        self.status = "queued"
        self.id = id
        self.video_progress = 0
        self.motion_progress = 0
    
    def get_status(self):
        return self.status
    
    def get_id(self):
        return self.id
    
    def set_status(self, status):
        self.status = status

    def get_video_progress(self):
        return self.video_progress
    
    def get_frame_progress(self):
        return self.motion_progress

    def set_video_progress(self, progress: int):
        self.video_progress = progress

    def set_motion_progress(self, progress: int):
        self.motion_progress = progress

    def get_JSON(self):
        return {
            "clip_progress": self.video_progress,
            "motion_progress": self.motion_progress
        }
    
class JobManager():
    def __init__(self):
        self.jobs: List[Job] = []
    
    def is_empty(self):
        return len(self.jobs) == 0
    
    def exists(self, job_id):
        return job_id in [job.get_id() for job in self.jobs]

    def add_job(self, job_id):
        self.jobs.append(Job(job_id))

    def get_job(self, job_id):
        if self.exists(job_id):
            return [j for j in self.jobs if j.get_id() == job_id][0]
        else:
            return None
    
    def remove_job(self, job_id):
        if not self.is_empty():
            self.jobs = [job for job in self.jobs if job.get_id() != job_id]
                
    def get_job_status(self, job_id):
        job = self.get_job(job_id)
        return job.get_status() if job else None

manager = JobManager()