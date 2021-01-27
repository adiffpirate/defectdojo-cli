from datetime import datetime
import json
import sys
import argparse
import requests

class Engagements(object):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Perform <sub_command> related to engagements on DefectDojo',
            usage='''defect-dojo engagements <sub_command> [<args>]

    You can use the following sub_commands:
        create     Create an engagement (engagements create --help for more details)
        close      Close an engagement (engagements close --help for more details)
        update     Update an engagement (engagements update --help for more details)
''')
        parser.add_argument('sub_command', help='Sub_command to run')
        args = parser.parse_args(sys.argv[2:3]) # Get sub_command
        if not hasattr(self, args.sub_command):
            print('Unrecognized sub_command')
            parser.print_help()
            exit(1)
        # Use dispatch pattern to invoke method with same name
        getattr(self, args.sub_command)()

    def create(self):
        parser = argparse.ArgumentParser(description='Create an engagement on DefectDojo',
                                         usage='defect-dojo engagements create [<args>]')
        required = parser.add_argument_group('required arguments')
        required.add_argument('--url', help='DefectDojo URL', required=True)
        required.add_argument('--api_key', help='API v2 Key', required=True)
        required.add_argument('--name', help='Engagement name', required=True)
        required.add_argument('--desc', help='Engagement description', required=True, metavar='DESCRIPTION')
        required.add_argument('--product_id',
                              help='ID of the product on which the engagement will be created',
                              required=True)
        required.add_argument('--lead_id', help='ID of the user responsible for this engagement', required=True)
        parser.add_argument('--start_date', help='Engagement starting date (default = today())',
                            metavar='YYYY-MM-DD', default=datetime.now().strftime('%Y-%m-%d'))
        parser.add_argument('--end_date', help='Engagement ending date (default = today())',
                            metavar='YYYY-MM-DD', default=datetime.now().strftime('%Y-%m-%d'))
        parser.add_argument('--type', help='Engagement type (default = "CI/CD")',
                            choices=['Interactive', 'CI/CD'], default='CI/CD')
        parser.add_argument('--repo_url', help='Link to source code',
                            default='')
        parser.add_argument('--branch_tag', help='Tag or branch of the product the engagement tested',
                            metavar='TAG_OR_BRANCH', default='')
        parser.add_argument('--product_version', help='Version of the product the engagement tested',
                            default='')
        parser.add_argument('--status', help='Engagement status (default = "In Progress")',                                                     choices=['Not Started', 'Blocked', 'Cancelled', 'Completed', 'In Progress',
                                     'On Hold', 'Waiting for Resource'],
                            default='In Progress')

        # Parse out arguments ignoring the first three (because we're inside a sub_command)
        args = vars(parser.parse_args(sys.argv[3:]))
        self.url = args['url']
        self.api_key = args['api_key']
        self.name = args['name']
        self.desc = args['desc']
        self.product_id = args['product_id']
        self.lead_id = args['lead_id']
        self.start_date = args['start_date']
        self.end_date = args['end_date']
        self.type = args['type']
        self.repo_url = args['repo_url']
        self.branch_tag = args['branch_tag']
        self.product_version = args['product_version']
        self.status = args['status']

        API_URL = self.url+'/api/v2'
        ENGAGEMENTS_URL = API_URL+'/engagements/'
        AUTH_TOKEN = 'Token '+self.api_key

        headers = dict()
        request_json = dict()

        # Prepare headers
        headers['Authorization'] = AUTH_TOKEN

        request_json['name'] = self.name
        request_json['description'] = self.desc
        request_json['product'] = self.product_id
        request_json['lead'] = self.lead_id
        request_json['target_start'] = self.start_date
        request_json['target_end'] = self.end_date
        request_json['engagement_type'] = self.type
        request_json['source_code_management_uri'] = self.repo_url
        request_json['branch_tag'] = self.branch_tag
        request_json['version'] = self.product_version
        request_json['status'] = self.status

        # Make a request to API
        response = requests.post(ENGAGEMENTS_URL, headers=headers, data=request_json)
        self.output = json.loads(response.text)
        self.pretty_output = json.dumps(self.output, indent=4)
        print(self.pretty_output)

        if response.status_code == 201:
            # Sucess
            exit(0)
        else:
            # Failure
            exit(1)

    def close(self):
        parser = argparse.ArgumentParser(description='Close an engagement on DefectDojo',
                                         usage='defect-dojo engagements close ENGAGEMENT_ID')
        parser.add_argument('engagement_id', help='ID of the engagement to be updated')
        required = parser.add_argument_group('required arguments')
        required.add_argument('--url', help='DefectDojo URL', required=True)
        required.add_argument('--api_key', help='API v2 Key', required=True)

        # Parse out arguments ignoring the first three (because we're inside a sub_command)
        args = vars(parser.parse_args(sys.argv[3:]))
        self.engagement_id = args['engagement_id']
        self.url = args['url']
        self.api_key = args['api_key']

        API_URL = self.url+'/api/v2'
        ENGAGEMENTS_URL = API_URL+'/engagements/'
        ENGAGEMENTS_ID_URL = ENGAGEMENTS_URL+str(self.engagement_id)
        ENGAGEMENTS_CLOSE_URL = ENGAGEMENTS_ID_URL+'/close/'
        AUTH_TOKEN = 'Token '+self.api_key

        headers = dict()

        # Prepare headers
        headers['Authorization'] = AUTH_TOKEN

        # Make a request to API
        response = requests.post(ENGAGEMENTS_CLOSE_URL, headers=headers)

        if response.status_code == 200:
            # Sucess
            self.output = json.loads('{"return": "sucess"}')
            self.pretty_output = json.dumps(self.output, indent=4)
            print(self.pretty_output)
            exit(0)
        else:
            # Failure
            self.output = json.loads(response.text)
            self.pretty_output = json.dumps(self.output, indent=4)
            print(self.pretty_output)
            exit(1)

    def update(self):
        parser = argparse.ArgumentParser(description='Update a engagement on DefectDojo',
                                         usage='defect-dojo engagements update ENGAGEMENT_ID [<args>]')
        parser.add_argument('engagement_id', help='ID of the engagement to be updated')
        required = parser.add_argument_group('required arguments')
        required.add_argument('--url', help='DefectDojo URL', required=True)
        required.add_argument('--api_key', help='API v2 Key', required=True)
        parser.add_argument('--name', help='Engagement name')
        parser.add_argument('--desc', help='Engagement description', metavar='DESCRIPTION')
        parser.add_argument('--product_id', help='ID of the product the engagement belongs to')
        parser.add_argument('--lead_id', help='ID of the user responsible for this engagement')
        parser.add_argument('--start_date', help='Engagement starting date', metavar='YYYY-MM-DD')
        parser.add_argument('--end_date', help='Engagement ending date', metavar='YYYY-MM-DD')
        parser.add_argument('--type', help='Engagement type', choices=['Interactive', 'CI/CD'])
        parser.add_argument('--repo_url', help='Link to source code')
        parser.add_argument('--branch_tag', help='Tag or branch of the product the engagement tested',
                            metavar='TAG_OR_BRANCH')
        parser.add_argument('--product_version', help='Version of the product the engagement tested')
        parser.add_argument('--status', help='Engagement status',
                            choices=['Not Started', 'Blocked', 'Cancelled', 'Completed', 'In Progress',
                                     'On Hold', 'Waiting for Resource'])

        request_json = dict()
        # Parse out arguments ignoring the first three (because we're inside a sub_command)
        # and fill up JSON to be send
        args = vars(parser.parse_args(sys.argv[3:]))
        self.engagement_id = args['engagement_id']
        self.url = args['url']
        self.api_key = args['api_key']
        if args['name'] is not None:
            self.name = args['name']
            request_json['name'] = self.name
        if args['desc'] is not None:
            self.desc = args['desc']
            request_json['description'] = self.desc
        if args['product_id'] is not None:
            self.product_id = args['product_id']
            request_json['product'] = self.product_id
        if args['lead_id'] is not None:
            self.lead_id = args['lead_id']
            request_json['lead'] = self.lead_id
        if args['start_date'] is not None:
            self.start_date = args['start_date']
            request_json['target_start'] = self.start_date
        if args['end_date'] is not None:
            self.end_date = args['end_date']
            request_json['target_end'] = self.end_date
        if args['type'] is not None:
            self.type = args['type']
            request_json['engagement_type'] = self.type
        if args['repo_url'] is not None:
            self.repo_url = args['repo_url']
            request_json['source_code_management_uri'] = self.repo_url
        if args['branch_tag'] is not None:
            self.branch_tag = args['branch_tag']
            request_json['branch_tag'] = self.branch_tag
        if args['product_version'] is not None:
            self.product_version = args['product_version']
            request_json['version'] = self.product_version
        if args['status'] is not None:
            self.status = args['status']
            request_json['status'] = self.status

        API_URL = self.url+'/api/v2'
        ENGAGEMENTS_URL = API_URL+'/engagements/'
        ENGAGEMENTS_ID_URL = ENGAGEMENTS_URL+str(self.engagement_id)
        AUTH_TOKEN = 'Token '+self.api_key

        headers = dict()

        # Prepare headers
        headers['Authorization'] = AUTH_TOKEN

        # Make a request to API
        response = requests.patch(ENGAGEMENTS_ID_URL, headers=headers, data=request_json)
        self.output = json.loads(response.text)
        self.pretty_output = json.dumps(self.output, indent=4)
        print(self.pretty_output)

        if response.status_code == 200:
            # Sucess
            exit(0)
        else:
            # Failure
            exit(1)
