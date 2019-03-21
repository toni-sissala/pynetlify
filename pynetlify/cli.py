import sys
import argparse
from pynetlify import pynetlify


def create_site(netlify_api, args):
    site = netlify_api.create_site()
    print(site)


def list_sites(netlify_api, args):
    for site in netlify_api.sites():
        print(site)


def delete_site(netlify_api, args):
    netlify_api.delete_site(pynetlify.Site(
        name=None, url=None,
        id=args.site_id))


def cli_main():
    parser = argparse.ArgumentParser(description='Interact with Netlify API.')
    parser.add_argument('--auth-token', required=True, type=str,
                        help='Netlify Authentication Token')
    subparsers = parser.add_subparsers(help='subcmd help',
                                       dest='action')
    subparsers.add_parser('create_site')
    subparsers.add_parser('list_sites')
    delete_site_parser = subparsers.add_parser('delete_site')
    delete_site_parser.add_argument('site_id', type=str)
    args = parser.parse_args()
    available_actions = {'create_site': create_site,
                         'delete_site': delete_site,
                         'list_sites': list_sites}
    selected_action = available_actions.get(args.action)
    if not selected_action:
        print("Select action: %s" %
              (', '.join(available_actions.keys()),))
        return 1
    netlify_api = pynetlify.APIRequest(args.auth_token)
    selected_action(netlify_api, args)
    return 0
