import logging
from typing import Union, TYPE_CHECKING

from facturator.domain import commands, events
from facturator.service_layer import handlers, unit_of_work

if TYPE_CHECKING:
    from . import unit_of_work

logger = logging.getLogger(__name__)

Message = Union[commands.Command, events.Event]


def handle(
    message: Message,
    uow: unit_of_work.AbstractUnitOfWork
):
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, commands.Command):
            cmd_output = handle_command(message, uow)
            results.append(cmd_output)
        else:
            raise Exception(f"{message} is not a command")
    return results


def handle_command(
        command: commands.Command,
        uow: unit_of_work.AbstractUnitOfWork,
):
    logger.debug("handling command {}".format(command))
    try:
        handler = COMMAND_HANDLERS[type(command)]
        result = handler(command, uow=uow)
        return result
    except Exception:
        logger.exception("Exception happened while handling {}".format(command))
        raise



COMMAND_HANDLERS = {
    commands.AddPayer: handlers.add_payer,
    commands.AddOrder: handlers.add_order,
    commands.UploadOrders: handlers.upload_payment_orders_from_file,
}
