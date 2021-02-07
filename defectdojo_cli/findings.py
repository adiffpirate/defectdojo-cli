from datetime import datetime
import json
import sys
import argparse
import requests
from defectdojo_cli.util import Util

class Findings(object):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Perform <sub_command> related to findings on DefectDojo',
            usage='''defectdojo findings <sub_command> [<args>]

    You can use the following sub_commands:
        upload          Upload findings (scan results)
        list            List findings
        print_scanners  Print a list of possible entries for the --scanner flag
''')
        parser.add_argument('sub_command', help='Sub_command to run',
                            choices=['upload', 'list', 'print_scanners'])
        # Get sub_command
        args = parser.parse_args(sys.argv[2:3])
        # Use dispatch pattern to invoke method with same name (that starts with _)
        getattr(self, '_'+args.sub_command)()

    def print_scanners(self):
        for scanner in Util().ACCEPTED_SCANS:
            print(scanner)
        exit(0)

    def upload(self, **kwargs):
        args = dict()
        # Parse arguments
        for key,value in kwargs.items():
            args[key] = value
        # Prepare JSON data to be send
        request_json = dict()
        API_URL = args['url']+'/api/v2'
        IMPORT_SCAN_URL = API_URL+'/import-scan/'
        request_json['scan_date'] = datetime.now().strftime('%Y-%m-%d')
        request_json['scan_type'] = args['scanner']
        request_json['verified'] = args['verified']
        request_json['engagement'] = args['engagement_id']
        request_json['lead'] = args['lead_id']
        request_json['active'] = args['active']
        request_json['minimum_severity'] = args['min_severity']
        if args['tag'] is not None:
            request_json['tags'] = args['tag']
        # Prepare file data to be send
        files = dict()
        files['file'] = open(args['result_file'])
        # Make request
        response = Util().request_apiv2('POST', IMPORT_SCAN_URL, args['api_key'], files=files, data=request_json)
        return response

    def _upload(self):
        # Read user-supplied arguments
        parser = argparse.ArgumentParser(description='Upload findings (scan results) to DefectDojo',
                                         usage='defectdojo findings upload RESULT_FILE [<args>]')
        optional = parser._action_groups.pop()
        required = parser.add_argument_group('required arguments')
        parser.add_argument('result_file', help='File with the results to be uploaded')
        required.add_argument('--scanner', help='Type of scanner',
                              choices=Util().ACCEPTED_SCANS, metavar='SCANNER', required=True)
        required.add_argument('--url', help='DefectDojo URL', required=True)
        required.add_argument('--api_key', help='API v2 Key', required=True)
        required.add_argument('--engagement_id', help='Engagement ID', required=True)
        required.add_argument('--lead_id', help='ID of the user conducting the operation', required=True)
        optional.add_argument('--active', help='Mark vulnerabilities found as active (default)',
                              action='store_true', dest='active')
        optional.add_argument('--inactive', help='Mark vulnerabilities found as inactive',
                              action='store_false', dest='active')
        optional.add_argument('--verified', help='Mark vulnerabilities found as verified',
                              action='store_true', dest='verified')
        optional.add_argument('--unverified', help='Mark vulnerabilities found as unverified (default)',
                              action='store_false', dest='verified')
        optional.set_defaults(active=True, verified=False)
        optional.add_argument('--min_severity', help='Ignore findings below this severity (default = "Low")',
                              choices=['Informational', 'Low', 'Medium', 'High', 'Critical'], default='Low')
        optional.add_argument('--tag', help='Scanner tag (can be used multiple times)', action='append')
        optional.add_argument('--auto_close', help='Close all the open findings from --scanner and '+
                              '--engagement_id that are not listed in this upload (requires deduplication)',
                              action='store_true', default=False)
        parser._action_groups.append(optional)
        # Parse out arguments ignoring the first three (because we're inside a sub-command)
        args = vars(parser.parse_args(sys.argv[3:]))
        # Upload results
        response = self._upload(**args)
        # Print output
        if args['auto_close']:
            if response.status_code == 201: #Success
                # Pretty print JSON response
                Util().default_output(response, sucess_status_code=201)
        else:
            # Pretty print JSON response
            Util().default_output(response, sucess_status_code=201)

    def list(self, **kwargs):
        args = dict()
        # Parse arguments
        for key,value in kwargs.items():
            args[key] = value
        # Create parameters to be requested
        request_params = dict()
        API_URL = args['url']+'/api/v2'
        FINDINGS_URL = API_URL+'/findings/'
        if args['id'] is not None:
            request_params['id'] = args['id']
        if args['product_id'] is not None:
            request_params['test__engagement__product'] = args['product_id']
        if args['engagement_id'] is not None:
            request_params['test__engagement'] = args['engagement_id']
        if args['scanner'] is not None:
            # In order to filter scanner we need to get its ID via API
            temp_params = dict()
            temp_params['name'] = args['scanner']
            # Make a get request to /test_types passing the scanner as parameter
            temp_response = Util().request_apiv2('GET', API_URL+'/test_types/', args['api_key'], params=temp_params)
            # Tranform the above response in json and get the id
            scanner_id = json.loads(temp_response.text)['results'][0]['id']
            # Add to request_params
            request_params['test__test_type'] = scanner_id
        if args['active'] is not None:
            if args['active'] is True:
                request_params['active'] = 2
            if args['active'] is False:
                request_params['active'] = 3
        if args['valid'] is not None:
            if args['valid'] is True:
                request_params['false_p'] = 3
            if args['valid'] is False:
                request_params['false_p'] = 2
        if args['scope'] is not None:
            if args['scope'] is True:
                request_params['out_of_scope'] = 3
            if args['scope'] is False:
                request_params['out_of_scope'] = 2
        if args['limit'] is not None:
            request_params['limit'] = args['limit']
        else:
            # Make a request to API getting only one finding to retrieve the total amount of findings
            temp_params = args.copy()
            temp_params['limit'] = 1
            temp_response = self.list(**temp_params)
            limit = int(json.loads(temp_response.text)['count'])
            request_params['limit'] = limit
        # Make request
        response = Util().request_apiv2('GET', FINDINGS_URL, args['api_key'], params=request_params)
        return response

    def _list(self):
        # Read user-supplied arguments
        parser = argparse.ArgumentParser(description='List findings stored on DefectDojo',
                                         usage='defectdojo findings list [<args>]')
        optional = parser._action_groups.pop()
        required = parser.add_argument_group('required arguments')
        required.add_argument('--url', help='DefectDojo URL', required=True)
        required.add_argument('--api_key', help='API v2 Key', required=True)
        optional.add_argument('--id', help='Get finding with this id')
        optional.add_argument('--product_id', help='Filter by product')
        optional.add_argument('--engagement_id', help='Filter by engagement')
        optional.add_argument('--scanner', help='Filter by scanner',
                              choices=Util().ACCEPTED_SCANS, metavar='SCANNER')
        optional.add_argument('--active', help='List only actives findings',
                            action='store_true', dest='active')
        optional.add_argument('--inactive', help='List only inactives findings',
                            action='store_false', dest='active')
        optional.add_argument('--valid', help='List only valid findings (true-positives)',
                            action='store_true', dest='valid')
        optional.add_argument('--false_positives', help='List only false-positives findings',
                            action='store_false', dest='valid')
        optional.add_argument('--in_scope', help='List only findings in-scope',
                            action='store_true', dest='scope')
        optional.add_argument('--out_of_scope', help='List only findings out-of-scope',
                            action='store_false', dest='scope')
        optional.add_argument('--json', help='Print output in JSON format', action='store_true', default=False)
        optional.add_argument('--limit',
                              help='Number of results to return (by default it gets all the findings)')
        optional.add_argument('--offset', help='The initial index from which to return the results '
                              +'(not needed if the --limit flag is not set)')
        optional.set_defaults(active=None, valid=None, scope=None)
        parser._action_groups.append(optional)
        # Parse out arguments ignoring the first three (because we're inside a sub-command)
        args = vars(parser.parse_args(sys.argv[3:]))
        # Get findings
        response = self.list(**args)
        # Print output
        json_out = json.loads(response.text)
        if response.status_code == 200: # Sucess
            if args['json'] is True: # If --json flag is used
                # Pretty print output in json
                pretty_json_out = json.dumps(json_out, indent=4)
                print(pretty_json_out)
            else:
                # Print output in a more human readable way
                criticals = []
                highs = []
                mediums = []
                lows = []
                infos = []
                for finding in json_out['results']:
                    if finding['severity'] == 'Critical':
                        criticals.append(finding)
                    if finding['severity'] == 'High':
                        highs.append(finding)
                    if finding['severity'] == 'Medium':
                        mediums.append(finding)
                    if finding['severity'] == 'Low':
                        lows.append(finding)
                    if finding['severity'] == 'Info':
                        infos.append(finding)
                if criticals:
                    print('#################### CRITICAL ####################')
                    for finding in criticals:
                        print('\n'+str(finding['title']))
                        print(args['url']+'/finding/'+str(finding['id']))
                    print('\n\n')
                if highs:
                    print('#################### HIGH ####################')
                    for finding in highs:
                        print('\n'+str(finding['title']))
                        print(args['url']+'/finding/'+str(finding['id']))
                    print('\n\n')
                if mediums:
                    print('#################### MEDIUM ####################')
                    for finding in mediums:
                        print('\n'+str(finding['title']))
                        print(args['url']+'/finding/'+str(finding['id']))
                    print('\n\n')
                if lows:
                    print('#################### LOW ####################')
                    for finding in lows:
                        print('\n'+str(finding['title']))
                        print(args['url']+'/finding/'+str(finding['id']))
                    print('\n\n')
                if infos:
                    print('#################### INFO ####################')
                    for finding in infos:
                        print('\n'+str(finding['title']))
                        print(args['url']+'/finding/'+str(finding['id']))
                    print('\n\n')
            exit(0)
        else: # Failure
            # Pretty print output in json
            pretty_json_out = json.dumps(json_out, indent=4)
            print(pretty_json_out)
            exit(1)
