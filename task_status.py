import sqlite3
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskQueue:
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                parent_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                subtask_data TEXT,
                status TEXT NOT NULL,
                priority INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                result TEXT,
                error_message TEXT
            )
        """)
        
        # Project state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_state (
                id TEXT PRIMARY KEY,
                project_name TEXT NOT NULL,
                objective TEXT NOT NULL,
                current_phase TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_project(self, project_name: str, objective: str) -> str:
        """Create a new project and return its ID."""
        project_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO project_state (id, project_name, objective, current_phase, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (project_id, project_name, objective, "planning", "{}"))
        
        conn.commit()
        conn.close()
        return project_id
    
    def add_task(self, title: str, description: str, subtask_data: Dict[str, Any], 
                 parent_id: Optional[str] = None, priority: int = 0) -> str:
        """Add a new task to the queue."""
        task_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO tasks (id, parent_id, title, description, subtask_data, status, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (task_id, parent_id, title, description, json.dumps(subtask_data), 
              TaskStatus.PENDING.value, priority))
        
        conn.commit()
        conn.close()
        return task_id
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """Get the next pending task with highest priority."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, parent_id, title, description, subtask_data, status, priority, created_at
            FROM tasks
            WHERE status = ?
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
        """, (TaskStatus.PENDING.value,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'parent_id': row[1],
                'title': row[2],
                'description': row[3],
                'subtask_data': json.loads(row[4]),
                'status': row[5],
                'priority': row[6],
                'created_at': row[7]
            }
        return None
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          result: Optional[str] = None, error_message: Optional[str] = None):
        """Update task status and result."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE tasks 
            SET status = ?, result = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status.value, result, error_message, task_id))
        
        conn.commit()
        conn.close()
    
    def get_project_state(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get current project state."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT project_name, objective, current_phase, metadata
            FROM project_state WHERE id = ?
        """, (project_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'project_name': row[0],
                'objective': row[1],
                'current_phase': row[2],
                'metadata': json.loads(row[3])
            }
        return None
    
    def update_project_phase(self, project_id: str, phase: str, metadata: Dict[str, Any] = None):
        """Update project phase and metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if metadata is None:
            metadata = {}
        
        cursor.execute("""
            UPDATE project_state 
            SET current_phase = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (phase, json.dumps(metadata), project_id))
        
        conn.commit()
        conn.close()
    
    def get_completed_tasks(self, parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all completed tasks, optionally filtered by parent_id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if parent_id:
            cursor.execute("""
                SELECT id, title, description, result, updated_at
                FROM tasks
                WHERE status = ? AND parent_id = ?
                ORDER BY updated_at ASC
            """, (TaskStatus.COMPLETED.value, parent_id))
        else:
            cursor.execute("""
                SELECT id, title, description, result, updated_at
                FROM tasks
                WHERE status = ?
                ORDER BY updated_at ASC
            """, (TaskStatus.COMPLETED.value,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{'id': row[0], 'title': row[1], 'description': row[2], 
                'result': row[3], 'updated_at': row[4]} for row in rows]
    
    def get_task_count_by_status(self) -> Dict[str, int]:
        """Get count of tasks by status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT status, COUNT(*) FROM tasks GROUP BY status
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return {row[0]: row[1] for row in rows}