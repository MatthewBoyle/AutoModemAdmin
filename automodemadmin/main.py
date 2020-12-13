import click
import modems


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
    try:
        modem = modems.get(model, {'ip_address': ip_address, 'username': username, 'password': password,
                                   'ignore_cert': ignore_cert})
        ctx['modem'] = modem
    except modems.UnknownModemModelError:
        print(f'Modem of model type {model} not known!')


@run.command()
@click.pass_context
def reboot(ctx):
    """Reboot the modem."""
    modem = ctx.obj['modem']
    try:
        modem.reboot()
    except Exception:
        # Log errors, then quit
        pass


@run.command()
@click.argument('page')
def get_page(ctx, page):
    """Make an HTTP request for the provided sub-URL at the modem's ip."""
    modem = ctx.obj['modem']
    try:
        modem.get_page(page)
    except Exception:
        # Log errors, then quit
        pass

@run.command()
def reset_wifi():
    pass

@run.command()
def migrate_channel():
    pass


if __name__ == "__main__":
    run({})
