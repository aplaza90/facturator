import logging
from typing import List, Dict, Callable, Type, Union, TYPE_CHECKING

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
        if isinstance(message, events.Event):
            handle_event(message, uow)
        elif isinstance(message, commands.Command):
            cmd_output = handle_command(message, uow)
            results.append(cmd_output)
        else:
            raise Exception(f"{message} is not event or command")
    return results


def handle_event(
        event: events.Event,
        queue: List[Message],
        uow: unit_of_work.AbstractUnitOfWork,
):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            logger.debug("Handling event {}".format(event))
            handler(event, uow=uow)
        except Exception:
            logger.exception("something happened while handling {}".format(event))
            continue


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


EVENT_HANDLERS = {
    events.RepeatedPayer: [handlers.send_repeated_payer_notification]
}


COMMAND_HANDLERS = {
    commands.AddPayer: handlers.add_payer,
    commands.AddOrder: handlers.add_order,
    commands.UploadOrders: handlers.upload_payment_orders_from_file,
}

