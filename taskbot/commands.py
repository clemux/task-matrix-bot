import logging
from datetime import datetime

from taskw import TaskWarrior

logger = logging.getLogger(__name__)


class BaseCommand:
    def __init__(self):
        self.w = TaskWarrior()

    def process(self, args):
        raise NotImplementedError

    def _task_id_exists(self, id: int):
        tasks = self.w.load_tasks()['pending']
        ids = [t['id'] for t in tasks]
        return id in ids

    @staticmethod
    def _parse_date(date_string):
        date = datetime.strptime(date_string, '%Y%m%dT%H%M%SZ')
        return date


class ListCommand(BaseCommand):
    def process(self, args):
        task_list = self.w.load_tasks()

        response = [f"**Current tasks**:"]
        for task in task_list['pending']:
            date = datetime.strptime(task['entry'], '%Y%m%dT%H%M%SZ')
            response.append(f"**{task['id']}** {date}: {task['description']}")
        return '\n\n'.join(response)


class AddCommand(BaseCommand):
    def process(self, args):
        description = args
        self.w.task_add(description=description)
        return f"Task added."


class DoneCommand(BaseCommand):
    def process(self, args: str):
        id = int(args)
        if self._task_id_exists(id):
            self.w.task_done(id=id)
            return f"Task {id} done."
        else:
            return f"No pending task matching ID {id}."


class InfoCommand(BaseCommand):
    def process(self, args: str):
        id = int(args)
        if not self._task_id_exists(id):
            return f"No pending task matching ID {id}."
        task = self.w.get_task(id=id)
        _, task_data = task
        logger.debug(task_data)
        due = task_data.get('due')
        return f"[{id}] - {task_data['description']} {f' - **due**: {self._parse_date(due)}' if due else ''}"


task_commands = {
    'list': ListCommand,
    'add': AddCommand,
    'done': DoneCommand,
    'info': InfoCommand,
}
