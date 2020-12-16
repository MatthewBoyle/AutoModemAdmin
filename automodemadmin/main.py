import click
import modems
import requests
import logging


@click.group()
@click.pass_context
@click.help_option('-h', '--help')
@click.option('-m', '--model', required=True, help="The manufacturer's model number.")
@click.option('-i', '--ip_address', required=True, help='The ip_address the modem is located at.')
@click.option('-u', '--username', default='admin', help='The username for modem administration.')
@click.option('-x', '--ignore_cert', is_flag=True, help='Ignore checking for certificate validity. '
                                                        'NOT RECOMMENDED!')
@click.password_option('-p', '--password', help='The password for modem administration.')
def run(ctx, model, ip_address, username, password, ignore_cert):
    ctx.ensure_object(dict)
    logging.basicConfig(filename='AutoModemAdmin.log', level=logging.INFO,
                        format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    try:
        modem = modems.get(model, {'ip_address': ip_address, 'username': username, 'password': password,
                                   'ignore_cert': ignore_cert})
        ctx.obj['modem'] = modem
    except modems.UnknownModemModelError as e:
        logging.exception('Invalid model!')


@run.command()
@click.pass_context
def reboot(ctx):
    """Reboot the modem."""
    modem = ctx.obj['modem']
    # TODO: Refactor try...except block into a ContextManager
    try:
        modem.reboot()
    except requests.RequestException as re:
        interrogate_requests_exception(re)


@run.command()
@click.argument('page')
@click.pass_context
def get_page(ctx, page):
    """Make an HTTP request for the provided sub-URL at the modem's ip."""
    modem = ctx.obj['modem']
    try:
        modem.get_page(page)
    except requests.RequestException as re:
        interrogate_requests_exception(re)


# @run.command()
# @clock.pass_context
# def reset_wifi():
#     pass


# @run.command()
# @click.pass_context
# def migrate_channel():
#     pass


def interrogate_requests_exception(re):
    """Write to the logfile the details of the response included in the RequestsException"""
    logging.exception(re)
    msg = ''
    responses = [re.response] if re.response else []
    try:  # We want to add any redirects from the history to the list of responses if they exist
        if re.response and re.response.history:
            responses += re.response.history.reverse()
    except AttributeError:
        pass
    for r in responses:
        msg = '\n'.join([f"Response URL: {r.url}",
                         f"Status: {r.status_code} {r.reason}",
                         f"Response Headers:\n{r.headers}",
                         f"Response Content:\n{r.text}\n\n"])
    logging.debug(msg)


if __name__ == '__main__':
    try:
        run(obj={})
    # Potential anti-pattern (you rarely want to catch ALL exceptions), but since this is the 'main' block and
    # I re-raise the exception, I will make an exception this one time (pun!?)
    except Exception as e:
        # Fun fact: logging.exception automatically includes traceback
        logging.exception("Critical Error! Full message below:")
        raise
