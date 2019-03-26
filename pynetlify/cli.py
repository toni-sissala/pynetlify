import os
import logging
import argparse
import configparser
from pynetlify import pynetlify


def deploy_folder(netlify_api, args):
    netlify_api.deploy_folder_to_site(
        args.folder,
        pynetlify.Site(name=None, url=None, id=args.site_id),
        args.force_all)


def create_site(netlify_api, args):
    site_properties = {}
    if args.name:
        site_properties.update({'name': args.name})
    if args.domain:
        site_properties.update({'custom_domain': args.domain})
    site = netlify_api.create_site(site_properties)
    print(site)


def list_sites(netlify_api, args):
    for site in netlify_api.sites():
        print(site)


def delete_site(netlify_api, args):
    netlify_api.delete_site(pynetlify.Site(
        name=None, url=None,
        id=args.site_id))


def delete_all_sites(netlify_api, args):
    for site in netlify_api.sites():
        netlify_api.delete_site(site)


def cli_main():
    argparser = argparse.ArgumentParser(
        description='Interact with Netlify API.')
    subparsers = argparser.add_subparsers(help='action help', dest='action')
    subparsers.required = True
    argparser.add_argument('--auth-token', type=str,
                           help='Netlify Authentication Token')
    argparser.add_argument('--loglevel', default='INFO', choices=[
        'DEBUG', 'INFO', 'WARN', 'ERROR'])
    available_actions = {'create_site': create_site,
                         'delete_site': delete_site,
                         'delete_all_sites': delete_all_sites,
                         'deploy_folder': deploy_folder,
                         'list_sites': list_sites}
    deploy_folder_parser = subparsers.add_parser('deploy_folder')
    deploy_folder_parser.add_argument('--site-id', required=True,
                                      type=str)
    deploy_folder_parser.add_argument('--force-all', action='store_true')
    deploy_folder_parser.add_argument('folder', type=str)
    create_site_parser = subparsers.add_parser('create_site')
    create_site_parser.add_argument('--name', type=str,
                                    help='Site name')
    create_site_parser.add_argument('--domain', type=str,
                                    help='Site domain')
    subparsers.add_parser('list_sites')
    delete_site_parser = subparsers.add_parser('delete_site')
    subparsers.add_parser('delete_all_sites')
    delete_site_parser.add_argument('site_id', type=str)
    args = argparser.parse_args()
    mod_dir = os.path.dirname(__file__)
    cwd = os.getcwd()
    conf_filename = 'pynetlify.ini'
    configfile_paths = [
        os.path.join(cwd, conf_filename),
        os.path.join(mod_dir, conf_filename)]
    config = configparser.ConfigParser()
    for c_filepath in configfile_paths:
        if os.path.exists(c_filepath):
            config.read(c_filepath)
    # TODO: inform user of missing auth-token
    auth_token = args.auth_token or config.get('netlify', 'auth-token')
    logging.basicConfig(level=getattr(logging, args.loglevel))
    selected_action = available_actions.get(args.action)
    netlify_api = pynetlify.APIRequest(auth_token)
    selected_action(netlify_api, args)
    return 0
