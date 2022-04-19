import logging
from datetime import datetime

from taskw import TaskWarrior

logger = logging.getLogger(__name__)


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

    def add(self, args: str):
        description = args
        self.w.task_add(description=description)
        return f"Task added."

    def done(self, args: str):
        id = int(args)
        if self._task_id_exists(id):
            self.w.task_done(id=id)
            return f"Task {id} done."
        else:
            return f"No pending task matching ID {id}."

    def delete(self, args: str):
        id = args
        self.w.task_delete(id=id)
        return f"Task {id} deleted."

    def info(self, args: str):
        id = int(args)
        if not self._task_id_exists(id):
            return f"No pending task matching ID {id}."
        task = self.w.get_task(id=id)
        _, task_data = task
        logger.debug(task_data)
        due = task_data.get('due')
        return f"[{id}] - {task_data['description']} {f' - **due**: {self._parse_date(due)}' if due else ''}"

    def _task_id_exists(self, id: int):
        tasks = self.w.load_tasks()['pending']
        ids = [t['id'] for t in tasks]
        return id in ids

    @staticmethod
    def _parse_date(date_string):
        date = datetime.strptime(date_string, '%Y%m%dT%H%M%SZ')
        return date


wrapper = TaskWrapper()

task_commands = {
    'list': wrapper.list,
    'add': wrapper.add,
    'done': wrapper.done,
    'info': wrapper.info,
}
