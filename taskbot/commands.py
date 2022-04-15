from datetime import datetime

from nio import AsyncClient, MatrixRoom, RoomMessageText
from taskw import TaskWarrior

from taskbot.chat_functions import react_to_event, send_text_to_room
from taskbot.config import Config
from taskbot.storage import Storage


class TaskWrapper:
    def __init__(self):
        self.w = TaskWarrior()

    def list(self):
        task_list = self.w.load_tasks()

        response = [f"**Current tasks**:"]
        for task in task_list['pending']:
            date = datetime.strptime(task['entry'], '%Y%m%dT%H%M%SZ')
            response.append(f"**{task['id']}** {date}: {task['description']}")
        return '\n\n'.join(response)

    def add(self, args):
        description = args
        self.w.task_add(description=description)
        return f"Task added."

    def done(self, args):
        id = args
        self.w.task_done(id=id)
        return f"Task {id} done."

wrapper = TaskWrapper()

task_commands = {
    'list': (wrapper.list, 0),
    'add': (wrapper.add, 1),
    'done': (wrapper.done, 1)
}
