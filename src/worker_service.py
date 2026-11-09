"""Bounded, restartable worker service for local deterministic jobs only."""
import json,signal,time
from src.job_runner import JobRunner

class WorkerService:
    def __init__(self,db_path,agent_id,mandate_id,poll_seconds=1,max_iterations=100):
        if poll_seconds<=0 or max_iterations<1:
            raise ValueError("bounded positive polling required")
        self.db_path=db_path
        self.agent_id=agent_id
        self.mandate_id=mandate_id
        self.poll_seconds=poll_seconds
        self.max_iterations=max_iterations
        self.stopping=False

    def stop(self,*_): self.stopping=True

    def run(self):
        summary={"attempts":0,"completed":[],"status":"STOPPED"}
        runner=JobRunner(self.db_path)
        try:
            for _ in range(self.max_iterations):
                if self.stopping: break
                summary["attempts"]+=1
                item=runner.run_once(self.agent_id,self.mandate_id)
                if item: summary["completed"].append(item["task_id"])
                elif self.poll_seconds: time.sleep(self.poll_seconds)
            summary["status"]="STOPPED" if self.stopping else "BOUNDED_EXIT"
            return summary
        finally:
            runner.close()
