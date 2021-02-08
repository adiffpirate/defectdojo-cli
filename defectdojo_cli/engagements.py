from datetime import datetime
import json
import sys
import argparse
import requests
from unittest.mock import PropertyMock
from defectdojo_cli.util import Util

class Engagements(object):
    def parse_cli_args(self):
        parser = argparse.ArgumentParser(
            description='Perform <sub_command> related to engagements on DefectDojo',
            usage='''defectdojo engagements <sub_command> [<args>]

    You can use the following sub_commands:
        create     Create an engagement (engagements create --help for more details)
        close      Close an engagement (engagements close --help for more details)
        update     Update an engagement (engagements update --help for more details)
''')
        parser.add_argument('sub_command', help='Sub_command to run',
                            choices=['create', 'close', 'update'])
        # Get sub_command
        args = parser.parse_args(sys.argv[2:3])
        # Use dispatch pattern to invoke method with same name (that starts with _)
        getattr(self, '_'+args.sub_command)()

    def create(self, **kwargs):
        args = dict()
        # Parse arguments
        for key,value in kwargs.items():
            args[key] = value
        # Prepare JSON data to be send
        request_json = dict()
        API_URL = args['url']+'/api/v2'
        ENGAGEMENTS_URL = API_URL+'/engagements/'
        request_json['name'] = args['name']
        request_json['description'] = args['desc']
        request_json['product'] = args['product_id']
        request_json['lead'] = args['lead_id']
        request_json['target_start'] = args['start_date']
        request_json['target_end'] = args['end_date']
        request_json['engagement_type'] = args['type']
        request_json['status'] = args['status']
        if args['repo_url'] is not None:
            request_json['source_code_management_uri'] = args['repo_url']
        if args['branch_tag'] is not None:
            request_json['branch_tag'] = args['branch_tag']
        if args['product_version'] is not None:
            request_json['version'] = args['product_version']
        # Make the request
        response = Util().request_apiv2('POST', ENGAGEMENTS_URL, args['api_key'], data=request_json)
        return response

    def _create(self):
        # Read user-supplied arguments
        parser = argparse.ArgumentParser(description='Create an engagement on DefectDojo',
                                         usage='defectdojo engagements create [<args>]')
        optional = parser._action_groups.pop()
        required = parser.add_argument_group('required arguments')
        required.add_argument('--url', help='DefectDojo URL', required=True)
        required.add_argument('--api_key', help='API v2 Key', required=True)
        required.add_argument('--name', help='Engagement name', required=True)
        required.add_argument('--desc', help='Engagement description', required=True, metavar='DESCRIPTION')
        required.add_argument('--product_id',
                              help='ID of the product on which the engagement will be created',
                              required=True)
        required.add_argument('--lead_id', help='ID of the user responsible for this engagement', required=True)
        optional.add_argument('--start_date', help='Engagement starting date (default = today())',
                            metavar='YYYY-MM-DD', default=datetime.now().strftime('%Y-%m-%d'))
        optional.add_argument('--end_date', help='Engagement ending date (default = today())',
                            metavar='YYYY-MM-DD', default=datetime.now().strftime('%Y-%m-%d'))
        optional.add_argument('--type', help='Engagement type (default = "CI/CD")',
                            choices=['Interactive', 'CI/CD'], default='CI/CD')
        optional.add_argument('--status', help='Engagement status (default = "In Progress")',                                                     choices=['Not Started', 'Blocked', 'Cancelled', 'Completed', 'In Progress',
                                     'On Hold', 'Waiting for Resource'],
                            default='In Progress')
        optional.add_argument('--repo_url', help='Link to source code')
        optional.add_argument('--branch_tag', help='Tag or branch of the product the engagement tested',
                            metavar='TAG_OR_BRANCH')
        optional.add_argument('--product_version', help='Version of the product the engagement tested')
        parser._action_groups.append(optional)
        # Parse out arguments ignoring the first three (because we're inside a sub_command)
        args = vars(parser.parse_args(sys.argv[3:]))
        # Create engagement
        response = self.create(**args)
        # Pretty print JSON response
        Util().default_output(response, sucess_status_code=201)

    def close(self, **kwargs):
        args = dict()
        # Parse arguments
        for key,value in kwargs.items():
            args[key] = value
        # Prepare parameters
        API_URL = args['url']+'/api/v2'
        ENGAGEMENTS_URL = API_URL+'/engagements/'
        ENGAGEMENTS_ID_URL = ENGAGEMENTS_URL+args['engagement_id']
        ENGAGEMENTS_CLOSE_URL = ENGAGEMENTS_ID_URL+'/close/'
        # Make the request
        response = Util().request_apiv2('POST', ENGAGEMENTS_CLOSE_URL, args['api_key'])
        return response

    def _close(self):
        # Read user-supplied arguments
        parser = argparse.ArgumentParser(description='Close an engagement on DefectDojo',
                                         usage='defectdojo engagements close ENGAGEMENT_ID')
        required = parser.add_argument_group('required arguments')
        parser.add_argument('engagement_id', help='ID of the engagement to be closed')
        required.add_argument('--url', help='DefectDojo URL', required=True)
        required.add_argument('--api_key', help='API v2 Key', required=True)
        # Parse out arguments ignoring the first three (because we're inside a sub_command)
        args = vars(parser.parse_args(sys.argv[3:]))
        # Close engagement
        response = self.close(**args)
        # DefectDojo doesnt has an output when a engagement is successfully closed so we need to create one
        if response.status_code == 200:
            type(response).text = PropertyMock(return_value='{"return": "sucess"}')
        # Pretty print JSON response
        Util().default_output(response, sucess_status_code=200)

    def update(self, **kwargs):
        args = dict()
        # Parse arguments
        for key,value in kwargs.items():
            args[key] = value
        # Prepare JSON data to be send
        request_json = dict()
        API_URL = args['url']+'/api/v2'
        ENGAGEMENTS_URL = API_URL+'/engagements/'
        ENGAGEMENTS_ID_URL = ENGAGEMENTS_URL+args['engagement_id']+'/'
        if args['name'] is not None:
            request_json['name'] = args['name']
        if args['desc'] is not None:
            request_json['description'] = args['desc']
        if args['product_id'] is not None:
            request_json['product'] = args['product_id']
        if args['lead_id'] is not None:
            request_json['lead'] = args['lead_id']
        if args['start_date'] is not None:
            request_json['target_start'] = args['start_date']
        if args['end_date'] is not None:
            request_json['target_end'] = args['end_date']
        if args['type'] is not None:
            request_json['engagement_type'] = args['type']
        if args['repo_url'] is not None:
            request_json['source_code_management_uri'] = args['repo_url']
        if args['branch_tag'] is not None:
            request_json['branch_tag'] = args['branch_tag']
        if args['product_version'] is not None:
            request_json['version'] = args['product_version']
        if args['status'] is not None:
            request_json['status'] = args['status']
        # Make the request
        response = Util().request_apiv2('PATCH', ENGAGEMENTS_ID_URL, args['api_key'], data=request_json)

    def _update(self):
        # Read user-supplied arguments
        parser = argparse.ArgumentParser(description='Update a engagement on DefectDojo',
                                         usage='defectdojo engagements update ENGAGEMENT_ID [<args>]')
        optional = parser._action_groups.pop()
        required = parser.add_argument_group('required arguments')
        parser.add_argument('engagement_id', help='ID of the engagement to be updated')
        required.add_argument('--url', help='DefectDojo URL', required=True)
        required.add_argument('--api_key', help='API v2 Key', required=True)
        optional.add_argument('--name', help='Engagement name')
        optional.add_argument('--desc', help='Engagement description', metavar='DESCRIPTION')
        optional.add_argument('--product_id', help='ID of the product the engagement belongs to')
        optional.add_argument('--lead_id', help='ID of the user responsible for this engagement')
        optional.add_argument('--start_date', help='Engagement starting date', metavar='YYYY-MM-DD')
        optional.add_argument('--end_date', help='Engagement ending date', metavar='YYYY-MM-DD')
        optional.add_argument('--type', help='Engagement type', choices=['Interactive', 'CI/CD'])
        optional.add_argument('--repo_url', help='Link to source code')
        optional.add_argument('--branch_tag', help='Tag or branch of the product the engagement tested',
                            metavar='TAG_OR_BRANCH')
        optional.add_argument('--product_version', help='Version of the product the engagement tested')
        optional.add_argument('--status', help='Engagement status',
                            choices=['Not Started', 'Blocked', 'Cancelled', 'Completed', 'In Progress',
                                     'On Hold', 'Waiting for Resource'])
        parser._action_groups.append(optional)
        # Parse out arguments ignoring the first three (because we're inside a sub_command)
        args = vars(parser.parse_args(sys.argv[3:]))
        # Update engagement
        response = self.update(**args)
        # Pretty print JSON response
        Util().default_output(response, sucess_status_code=200)
