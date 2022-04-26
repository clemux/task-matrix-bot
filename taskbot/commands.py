import logging
from datetime import datetime

from taskw import TaskWarrior

logger = logging.getLogger(__name__)


class BaseCommand:
    def __init__(self):
        self.w = TaskWarrior()

    async def process(self, args: str):
        raise NotImplementedError

    def _task_id_exists(self, id: int):
        tasks = self.w.load_tasks()['pending']
        ids = [t['id'] for t in tasks]
        return id in ids

    @staticmethod
    def _parse_date(date_string: str):
        date = datetime.strptime(date_string, '%Y%m%dT%H%M%SZ')
        return date

    @staticmethod
    def _format_date(date: datetime):
        delta = datetime.utcnow() - date
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if days:
            return f'{days}d'
        elif hours:
            return f'{hours}h'
        elif minutes:
            return f"{minutes}m"
        else:
            return f'{seconds}s'


class ListCommand(BaseCommand):
    async def process(self, args: str):
        task_list = self.w.load_tasks()
        pending_tasks = task_list['pending']
        if len(pending_tasks) == 0:
            return "No pending tasks."
        response = [f"**Current tasks**:"]
        for task in pending_tasks:
            date = datetime.strptime(task['entry'], '%Y%m%dT%H%M%SZ')
            formatted_date = self._format_date(date)
            response.append(f"**{task['id']}** - **{formatted_date}** - {task['description']}")
        return '\n\n'.join(response)


class AddCommand(BaseCommand):
    async def process(self, args: str):
        description = args
        task = self.w.task_add(description=description)
        return f"Task {task['id']} added."


class DoneCommand(BaseCommand):
    async def process(self, args: str):
        id = int(args)
        if self._task_id_exists(id):
            self.w.task_done(id=id)
            return f"Task {id} done."
        else:
            return f"No pending task matching ID {id}."


class InfoCommand(BaseCommand):
    async def process(self, args: str):
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
