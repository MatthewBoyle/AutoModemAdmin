import click
import os
import requests
import automodemadmin.modems as modems

@click.command()
@click.help_option('-h', '--help')
@click.option('-m', '--model')
@click.option('-i', '--ip_address')
@click.option('-a', '--action')
@click.option('-u', '--username')
@click.password_option('-p', '--password')
def run(ip_address, model, username, password, action):
    modem = modems.get(model, ip_address)
    modem.login(username, password)
    modem.do_action(action)


if __name__ == "__main__":
    # Parse command line args (admin, password, ip address, modem model)
    # Reboot modem
    run()
