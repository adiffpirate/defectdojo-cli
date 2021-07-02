from datetime import datetime
import json
import sys
import argparse
import requests
from unittest.mock import PropertyMock
from tabulate import tabulate
from defectdojo_cli.util import Util

class Tests(object):
    def parse_cli_args(self):
        parser = argparse.ArgumentParser(
            description='Perform <sub_command> related to tests on DefectDojo',
            usage='''defectdojo tests <sub_command> [<args>]

    You can use the following sub_commands:
        list            List tests
        update          Update a test
''')
        parser.add_argument(
            'sub_command',
            help='Sub_command to run'
        )
        # Get sub_command
        args = parser.parse_args(sys.argv[2:3])
        # Use dispatch pattern to invoke method with same name (that starts with _)
        getattr(self, '_'+args.sub_command)()

    def list(self, url, api_key, test_id=None, engagement_id=None,
             test_type=None, tag=None, limit=None, **kwargs):
        # Create parameters to be requested
        request_params = dict()
        API_URL = url+'/api/v2'
        TESTS_URL = API_URL+'/tests/'
        if test_id is not None:
            request_params['id'] = test_id
        if engagement_id is not None:
            request_params['engagement'] = engagement_id
        if test_type is not None:
            # In order to filter test_type we need to get its ID via API
            if type(test_type) is int:
                test_type_id = test_type
            else:
                temp_params = dict()
                temp_params['name'] = test_type
                # Make a get request to /test_types passing the test_type as parameter
                temp_response = Util().request_apiv2('GET', API_URL+'/test_types/', api_key, params=temp_params)
                # Tranform the above response in json and get the id
                test_type_id = json.loads(temp_response.text)['results'][0]['id']
            # Add to request_params
            request_params['test_type'] = test_type_id
        if tag is not None:
            if type(tag) is list:
                request_params['tags'] = ','.join(tag)
            else:
                request_params['tags'] = tag
        if limit is not None:
            request_params['limit'] = limit
        else:
            # Make a request to API getting only one test to retrieve the total amount of tests
            temp_params = request_params.copy()
            temp_params['url'] = url
            temp_params['api_key'] = api_key
            temp_params['limit'] = 1
            temp_response = self.list(**temp_params)
            limit = int(json.loads(temp_response.text)['count'])
            request_params['limit'] = limit

        # Make request
        response = Util().request_apiv2('GET', TESTS_URL, api_key, params=request_params)
        return response

    def _list(self):
        # Read user-supplied arguments
        parser = argparse.ArgumentParser(description='List tests stored on DefectDojo',
                                         usage='defectdojo tests list [<args>]')
        optional = parser._action_groups.pop()
        required = parser.add_argument_group('required arguments')
        required.add_argument(
            '--url',
            help='DefectDojo URL', required=True
        )
        required.add_argument(
            '--api_key',
            help='API v2 Key', required=True
        )
        optional.add_argument(
            '--id',
            help='Get tests with this id'
        )
        optional.add_argument(
            '--test_type',
            help='Filter by test type'
        )
        optional.add_argument(
            '--engagement_id',
            help='Filter by engagement'
        )
        optional.add_argument(
            '--tag',
            help='Test tag (can be used multiple times)', action='append'
        )
        optional.add_argument(
            '--limit',
            help='Number of results to return (by default it gets all the tests)'
        )
        optional.set_defaults(active=None, valid=None, scope=None)
        parser._action_groups.append(optional)
        # Parse out arguments ignoring the first three (because we're inside a sub-command)
        args = vars(parser.parse_args(sys.argv[3:]))

        # Adjust args
        if args['id'] is not None:
            # Rename key from 'id' to 'test_id' to match the argument of self.list
            args['test_id'] = args.pop('id')

        # Get tests
        response = self.list(**args)

        # Pretty print JSON response
        Util().default_output(response, sucess_status_code=200)

    def get_test_type_by_tags(self, url, api_key, tags, tags_operator, engagement_id=None):
        # First make a request to API getting all test types with the tags we're looking for
        request_params = dict()
        request_params['url'] = url
        request_params['api_key'] = api_key
        if engagement_id:
            request_params['engagement_id'] = engagement_id

        if tags_operator == 'union': # Default behaviour
            request_params['tag'] = tags
            response = self.list(**request_params)
            # Parse output
            json_out = json.loads(response.text)
            results = json_out['results']
            # Create set of all test types from the tag
            test_type_set = set()
            for test in results:
                test_type_set.add(test['test_type_name'])
            # Transform set to list
            test_type_list = list(test_type_set)

        elif tags_operator == 'intersect':
            test_type_list_of_sets = list()
            for tag in tags:
                request_params['tag'] = tag
                response = self.list(**request_params)
                # Parse output
                json_out = json.loads(response.text)
                results = json_out['results']
                # Create set of all test types from the tag
                test_type_set = set()
                for test in results:
                    test_type_set.add(test['test_type'])
                # Add set of test_type to list
                test_type_list_of_sets.append(test_type_set)

            # Get intersection between all sets
            test_type_intersection = test_type_list_of_sets[0]
            for test_type_set in test_type_list_of_sets[1:]:
                test_type_intersection.intersection_update(test_type_set)
            test_type_list = test_type_intersection

        return list(test_type_list)

    def update(self, url, api_key, test_id, title=None, desc=None,
               start_date=None, end_date=None, version=None, build_id=None,
               commit_hash=None, branch_tag=None, lead_id=None, test_type=None,
               environment=None, **kwargs):
        # Prepare JSON data to be send
        request_json = dict()
        API_URL = url+'/api/v2'
        TESTS_URL = API_URL+'/tests/'
        TESTS_ID_URL = TESTS_URL+test_id+'/'
        if title:
            request_json['title'] = title
        if desc:
            request_json['description'] = desc
        if start_date:
            request_json['target_start'] = start_date
        if end_date:
            request_json['target_end'] = end_date
        if version:
            request_json['version'] = version
        if build_id:
            request_json['build_id'] = build_id
        if commit_hash:
            request_json['commit_hash'] = commit_hash
        if branch_tag:
            request_json['branch_tag'] = branch_tag
        if lead_id:
            request_json['lead'] = lead_id
        if test_type:
            request_json['test_type'] = test_type
        if environment:
            request_json['enviroment'] = enviroment
        request_json = json.dumps(request_json)

        # Make the request
        response = Util().request_apiv2('PATCH', TESTS_ID_URL, api_key, data=request_json)
        return response

    def _update(self):
        # Read user-supplied arguments
        parser = argparse.ArgumentParser(description='Update a test on DefectDojo',
                                         usage='defectdojo tests update TEST_ID [<args>]')
        optional = parser._action_groups.pop()
        required = parser.add_argument_group('required arguments')

        parser.add_argument(
            'test_id', help='ID of the test to be updated'
        )

        required.add_argument(
            '--url', help='DefectDojo URL', required=True
        )

        required.add_argument(
            '--api_key', help='API v2 Key', required=True
        )

        optional.add_argument(
            '--title', help='Test title'
        )

        optional.add_argument(
            '--desc', help='Test description', metavar='DESCRIPTION'
        )

        optional.add_argument(
            '--start_date', help='Test starting date', metavar='YYYY-MM-DD'
        )

        optional.add_argument(
            '--end_date', help='Test ending date', metavar='YYYY-MM-DD'
        )

        optional.add_argument(
            '--version', help='Test version'
        )

        optional.add_argument(
            '--build_id', help='Test build ID'
        )

        optional.add_argument(
            '--commit_hash', help='Test commit hash'
        )

        optional.add_argument(
            '--test_type', help='Test type'
        )

        optional.add_argument(
            '--environment', help='Test environment'
        )

        optional.add_argument(
            '--branch_tag',
            help='Tag or branch of the product the engagement tested',
            metavar='TAG_OR_BRANCH'
        )

        optional.add_argument(
            '--lead_id', help='ID of the user responsible for this test'
        )

        parser._action_groups.append(optional)
        # Parse out arguments ignoring the first three (because we're inside a sub_command)
        args = vars(parser.parse_args(sys.argv[3:]))

        # Update engagement
        response = self.update(**args)

        # Pretty print JSON response
        Util().default_output(response, sucess_status_code=200)
