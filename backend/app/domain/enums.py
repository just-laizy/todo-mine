from enum import Enum

class TaskStatus(str, Enum):
    TODO = 'todo'
    IN_PROGRESS = 'in_progress'
    PENDING_REVIEWv = 'pending_review' 
    DONE = 'done'

class TaskPriority(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    ADVANCED = 'advanced'
    URGENT = 'urgent'


