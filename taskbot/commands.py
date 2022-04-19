from datetime import datetime

from nio import AsyncClient, MatrixRoom, RoomMessageText
from taskw import TaskWarrior

from taskbot.chat_functions import react_to_event, send_text_to_room
from taskbot.config import Config


class TaskWrapper:
    def __init__(self):
        self.w = TaskWarrior()

    def list(self, args):
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
        id = int(args)
        tasks = self.w.load_tasks()['pending']
        ids = [t['id'] for t in tasks]
        if id in ids:
            self.w.task_done(id=id)
            return f"Task {id} done."
        else:
            return f"No pending task matching ID {id}."

    def delete(self, args):
        id = args
        self.w.task_delete(id=id)
        return f"Task {id} deleted."

wrapper = TaskWrapper()

task_commands = {
    'list': wrapper.list,
    'add': wrapper.add,
    'done': wrapper.done,
}
