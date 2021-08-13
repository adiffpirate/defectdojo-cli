from datetime import datetime
import json
import sys
import argparse
import requests
import re
from unittest.mock import PropertyMock
from tabulate import tabulate
from defectdojo_cli.util import Util
from defectdojo_cli.engagements import Engagements
from defectdojo_cli.tests import Tests

class Findings(object):
    def parse_cli_args(self):
        parser = argparse.ArgumentParser(
            description='Perform <sub_command> related to findings on DefectDojo',
            usage='''defectdojo findings <sub_command> [<args>]

    You can use the following sub_commands:
        import          Import findings (scan results)
        upload          Same as import (deprecated, EOL december/2021)
        reimport        Re-import findings of a test
        list            List findings
        update          Update a finding
        close           Close a finding
''')
        parser.add_argument('sub_command', help='Sub_command to run')
        # Get sub_command
        args = parser.parse_args(sys.argv[2:3])
        if not hasattr(self, '_'+args.sub_command):
            print('Unrecognized sub_command')
            parser.print_help()
            exit(1)
        # Use dispatch pattern to invoke method with same name (that starts with _)
        getattr(self, '_'+args.sub_command)()

    # Backwards compability
    def _upload(self):
        self._import()

    def import_(self, url, api_key, result_file, scanner, engagement_id, lead_id,
               active=None, verified=None, scan_date=None, min_severity=None,
               tag_test=None, test_type=None, env=None, auto_close=None,
               skip_duplicates=None, version=None, build_id=None, branch_tag=None,
                commit_hash=None, **kwargs):
        # Prepare JSON data to be send
        request_json = dict()
        API_URL = url+'/api/v2'
        IMPORT_SCAN_URL = API_URL+'/import-scan/'
        if scan_date is not None:
            request_json['scan_date'] = scan_date
        if scanner is not None:
            request_json['scan_type'] = scanner
        if verified is not None:
            request_json['verified'] = verified
        if engagement_id is not None:
            request_json['engagement'] = engagement_id
        if lead_id is not None:
            request_json['lead'] = lead_id
        if active is not None:
            request_json['active'] = active
        if min_severity is not None:
            request_json['minimum_severity'] = min_severity
        if tag_test is not None:
            request_json['tags'] = tag_test
        if test_type is not None:
            request_json['test_type'] = test_type
        if env is not None:
            request_json['environment'] = env
        if auto_close is not None:
            request_json['close_old_findings'] = True
        if skip_duplicates is not None:
            request_json['skip_duplicates'] = True
        if version is not None:
            request_json['version'] = version
        if build_id is not None:
            request_json['build_id'] = build_id
        if branch_tag is not None:
            request_json['branch_tag'] = branch_tag
        if commit_hash is not None:
            request_json['commit_hash'] = commit_hash

        # Prepare file data to be send
        files = dict()
        files['file'] = open(result_file)

        # Make request
        response = Util().request_apiv2('POST', IMPORT_SCAN_URL, api_key,
                                        files=files, data=request_json)
        return response

    def _import(self):
        # Read user-supplied arguments
        parser = argparse.ArgumentParser(description='Import findings (scan results) to DefectDojo',
                                         usage='defectdojo findings import RESULT_FILE [<args>]')
        optional = parser._action_groups.pop()
        required = parser.add_argument_group('required arguments')
        parser.add_argument(
            'result_file',
            help='File with the results to be imported'
        )
        required.add_argument(
            '--scanner',
            help='Type of scanner',
            required=True
        )
        required.add_argument('--url', help='DefectDojo URL', required=True)
        required.add_argument('--api_key', help='API v2 Key', required=True)
        required.add_argument('--engagement_id', help='Engagement ID', required=True)
        required.add_argument('--lead_id', help='ID of the user conducting the operation', required=True)
        optional.add_argument('--test_type', help='Test type / title (default = scanner name)')
        optional.add_argument('--env', help='Environment')
        optional.add_argument('--scan_date', help='Date the scan was perfomed (default = TODAY)',
                              metavar='YYYY-MM-DD', default=datetime.now().strftime('%Y-%m-%d'))
        optional.add_argument('--active', help='Mark vulnerabilities found as active (default)',
                              action='store_true', dest='active')
        optional.add_argument('--inactive', help='Mark vulnerabilities found as inactive',
                              action='store_false', dest='active')
        optional.add_argument('--verified', help='Mark vulnerabilities found as verified',
                              action='store_true', dest='verified')
        optional.add_argument('--unverified', help='Mark vulnerabilities found as unverified (default)',
                              action='store_false', dest='verified')
        optional.set_defaults(active=True, verified=False)
        optional.add_argument('--min_severity', help='Ignore findings below this severity (default = "Info")',
                              choices=['Info', 'Low', 'Medium', 'High', 'Critical'], default='Info')
        optional.add_argument('--tag_test', help='Test tag (can be used multiple times)', action='append')
        optional.add_argument('--note',
                              help='Add the string passed to this flag as a'
                                   'note to each finding imported'
                                   '(can have a big impact on performance'
                                   'depending on the amount of findings'
                                   'imported)')
        optional.add_argument('--auto_close',
                              help='Close all open findings from the same '
                                  +'--test_type that are not listed on '
                                  +'this import (default = False)',
                              action='store_true')

        optional.add_argument(
            '--skip_duplicates',
            help='Dont import duplicates '
                 '(requires deduplication) (default = False)',
            action='store_true'
        )

        optional.add_argument(
            '--version',
            help='Current version of the project'
        )

        optional.add_argument(
            '--build_id',
            help='Build ID'
        )

        optional.add_argument(
            '--branch_tag',
            help='Branch or tag scanned'
        )

        optional.add_argument(
            '--commit_hash',
            help='Commit HASH'
        )
        parser._action_groups.append(optional)
        # Parse out arguments ignoring the first three (because we're inside a sub-command)
        args = vars(parser.parse_args(sys.argv[3:]))

        # Import results
        response = self.import_(**args)
        # Load import response as JSON
        out_error = False
        try:
            import_out = json.loads(response.text)
        except:
            out_error = True

        # If --note flag was passed
        if args['note'] is not None:
            # Get the findings that were imported 
            tmp_args = dict()
            tmp_args['url'] = args['url']
            tmp_args['api_key'] = args['api_key']
            tmp_args['test_id'] = import_out['test'] # Get the test ID from the import output
            tmp_response = self.list(**tmp_args)
            imported_findings_out = json.loads(tmp_response.text)
            # Create a list with all the imported findings IDs
            imported_findings_ids = set()
            for imported_finding in imported_findings_out['results']:
                imported_findings_ids.add(imported_finding['id'])
            # Add note to each imported finding
            tmp_args = dict()
            tmp_args['url'] = args['url']
            tmp_args['api_key'] = args['api_key']
            tmp_args['entry'] = args['note']
            for imported_finding_id in imported_findings_ids:
                tmp_args['finding_id'] = imported_finding_id
                self.add_note(**tmp_args)

        # Pretty print JSON response
        if not out_error:
            Util().default_output(response, sucess_status_code=201)
        else:
            print(response.text)

    def reimport(self, url, api_key, result_file, scanner, scan_date, test_id,
                  active=None, verified=None, min_severity=None, auto_close=None,
                  version=None, build_id=None, branch_tag=None, commit_hash=None,
                  **kwargs):
        # Prepare JSON data to be send
        request_json = dict()
        API_URL = url+'/api/v2'
        REIMPORT_SCAN_URL = API_URL+'/reimport-scan/'
        request_json['scan_type'] = scanner
        request_json['scan_date'] = scan_date
        request_json['test'] = test_id

        if active is not None:
            request_json['active'] = active
        if verified is not None:
            request_json['verified'] = verified
        if min_severity is not None:
            request_json['minimum_severity'] = min_severity
        if auto_close is not None:
            request_json['close_old_findings'] = True
        if version is not None:
            request_json['version'] = version
        if build_id is not None:
            request_json['build_id'] = build_id
        if branch_tag is not None:
            request_json['branch_tag'] = branch_tag
        if commit_hash is not None:
            request_json['commit_hash'] = commit_hash

        # Prepare file data to be send
        files = dict()
        files['file'] = open(result_file)

        # Make request
        response = Util().request_apiv2(
            'POST', REIMPORT_SCAN_URL, api_key, files=files, data=request_json
        )
        return response

    def _reimport(self):
        # Read user-supplied arguments
        parser = argparse.ArgumentParser(description='Re-import findings (scan results) to DefectDojo',
                                         usage='defectdojo findings reimport RESULT_FILE [<args>]')
        optional = parser._action_groups.pop()
        required = parser.add_argument_group('required arguments')

        parser.add_argument(
            'result_file',
            help='File with the results to be imported'
        )

        required.add_argument(
            '--scanner',
            help='Type of scanner',
            required=True
        )

        required.add_argument(
            '--url',
            help='DefectDojo URL',
            required=True
        )

        required.add_argument(
            '--api_key',
            help='API v2 Key',
            required=True
        )

        required.add_argument(
            '--test_id',
            help='Test to reimport',
            required=True
        )

        optional.add_argument(
            '--scan_date',
            help='Date the scan was perfomed (default = TODAY)',
            metavar='YYYY-MM-DD',
            default=datetime.now().strftime('%Y-%m-%d')
        )

        optional.add_argument(
            '--active',
            help='Mark vulnerabilities found as active (default)',
            action='store_true',
            dest='active'
        )

        optional.add_argument(
            '--inactive',
            help='Mark vulnerabilities found as inactive',
            action='store_false',
            dest='active'
        )

        optional.add_argument(
            '--verified',
            help='Mark vulnerabilities found as verified',
            action='store_true',
            dest='verified'
        )

        optional.add_argument(
            '--unverified',
            help='Mark vulnerabilities found as unverified (default)',
            action='store_false',
            dest='verified'
        )

        optional.set_defaults(active=True, verified=False)

        optional.add_argument(
            '--min_severity',
            help='Ignore findings below this severity (default = "Low")',
            choices=['Informational', 'Low', 'Medium', 'High', 'Critical'],
            default='Low'
        )

        optional.add_argument(
            '--auto_close',
            help='Close all open findings from the same --test_type that are '
                 'not listed on this import (default = False)',
            action='store_true'
        )

        optional.add_argument(
            '--version',
            help='Current version of the project'
        )

        optional.add_argument(
            '--build_id',
            help='Build ID'
        )

        optional.add_argument(
            '--branch_tag',
            help='Branch or tag scanned'
        )

        optional.add_argument(
            '--commit_hash',
            help='Commit HASH'
        )

        parser._action_groups.append(optional)

        # Parse out arguments ignoring the first three (because we're inside a sub-command)
        args = vars(parser.parse_args(sys.argv[3:]))
        # Re-import results
        response = self.reimport(**args)
        # Load re-import response as JSON
        out_error = False
        try:
            import_out = json.loads(response.text)
        except:
            out_error = True

        # Pretty print JSON response
        if not out_error:
            Util().default_output(response, sucess_status_code=201)
        else:
            print(response.text)


    def list(self, url, api_key, finding_id=None, test_id=None, product_id=None,
             engagement_id=None, test_type=None, active=None, closed=None,
             valid=None, scope=None, limit=None, tag_test=None, tags_operator=None, **kwargs):
        # Create parameters to be requested
        request_params = dict()
        API_URL = url+'/api/v2'
        FINDINGS_URL = API_URL+'/findings/'
        if finding_id is not None:
            request_params['id'] = finding_id
        if test_id is not None:
            request_params['test'] = test_id
        if product_id is not None:
            request_params['test__engagement__product'] = product_id
        if engagement_id is not None:
            request_params['test__engagement'] = engagement_id
        if active is not None:
            if active is True:
                request_params['active'] = 2
            elif active is False:
                request_params['active'] = 3
        if closed:
            request_params['is_Mitigated'] = True
        if valid is not None:
            if valid is True:
                request_params['false_p'] = 3
            elif valid is False:
                request_params['false_p'] = 2
        if scope is not None:
            if scope is True:
                request_params['out_of_scope'] = 3
            elif scope is False:
                request_params['out_of_scope'] = 2
        if limit is not None:
            request_params['limit'] = limit
        else:
            # Make a request to API getting only one finding to retrieve the total amount of findings
            temp_params = request_params.copy()
            temp_params['url'] = url
            temp_params['api_key'] = api_key
            temp_params['limit'] = 1
            temp_response = self.list(**temp_params)
            limit = int(json.loads(temp_response.text)['count'])
            request_params['limit'] = limit
        if tag_test:
            # First get all test types with the tags we're looking for
            test_type_list = Tests().get_test_type_by_tags(url, api_key, tag_test, tags_operator, engagement_id)
            # Add them to request parameters
            #   (so the tags aren't actually passed to request, only their test_types)
            if test_type is not None:
                # If a test_type was passed by the user, append it to the list
                test_type_list = test_type_list + test_type
            test_type = test_type_list
        if test_type is not None:
            # Transform test_type names to IDs
            test_type_ids = set()
            for tt in test_type:
                if type(tt) is str:
                    temp_params = dict()
                    temp_params['name'] = tt
                    # Make a get request to /test_types passing the test_type as parameter
                    temp_response = Util().request_apiv2('GET', API_URL+'/test_types/', api_key, params=temp_params)
                    # Tranform the above response in json and get the id
                    test_type_ids.add(json.loads(temp_response.text)['results'][0]['id'])
                else:
                    test_type_ids.add(tt)
            # If there's only one test_type
            if (len(test_type_ids) == 1):
                # Add to request_params
                request_params['test__test_type'] = list(test_type_ids)[0]
            else:
                # Use the appropriate method
                return self.list_multiple_test_types(url, api_key, test_type_ids, **request_params)

        # Make request
        response = Util().request_apiv2('GET', FINDINGS_URL, api_key, params=request_params)
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
        optional.add_argument('--test_id', help='Filter by test')
        optional.add_argument('--product_id', help='Filter by product')
        optional.add_argument('--engagement_id', help='Filter by engagement')
        optional.add_argument(
            '--test_type',
            help='Filter by test type (can be used multiple times)',
            action='append'
        )
        optional.add_argument('--active', help='List only actives findings',
                              action='store_true', dest='active')
        optional.add_argument('--inactive', help='List only inactives findings',
                              action='store_false', dest='active')
        optional.add_argument('--closed', help='List only closed/mitigated fidings',
                              action='store_true')
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
        optional.add_argument(
            '--fail_if_found',
            help='Returns a non-zero exit code if any findings with the passed '
                 'severity (or higher) are returned (default = NULL)',
            default='NULL',
            choices=['NULL', 'Info', 'Low', 'Medium', 'High', 'Critical']
        )
        optional.add_argument(
            '--tag_test',
            help='Test tag (can be used multiple times). The API call to '
                 'filter by tags is bugged, so what this does under the '
                 'hood is get all test_types from tests with theses tags and '
                 'filter by them. This method is not failproof, so if you are '
                 'having issues with it try fine-tuning using others flags '
                 '(e.g. passing an engagement id along with tags)',
            action='append'
        )
        optional.add_argument(
            '--tags_operator',
            help='Determine the operation to perform when working with multiple tags (default = "union")',
            default='union',
            choices=['union', 'intersect']
        )
        optional.set_defaults(active=None, valid=None, scope=None)
        parser._action_groups.append(optional)
        # Parse out arguments ignoring the first three (because we're inside a sub-command)
        args = vars(parser.parse_args(sys.argv[3:]))

        # Adjust args
        if args['id'] is not None:
            # Rename key from 'id' to 'finding_id' to match the argument of self.list
            args['finding_id'] = args.pop('id')

        # Get findings
        response = self.list(**args)

        # Print output
        json_out = json.loads(response.text)
        if response.status_code == 200: # Sucess

            if args['json'] is True: # If --json flag was passed
                # Pretty print output in json
                pretty_json_out = json.dumps(json_out, indent=4)
                print(pretty_json_out)

            else: # Print output in a more human readable way
                # Print findings amount
                findings_amount = json_out['count']
                print('\nFindings amount: '+str(json_out['count']))
                if findings_amount > 0:

                    # Print components and its version (usefull for Software Composition Analysis)
                    components = set()
                    for finding in json_out['results']:
                        if finding['component_name'] is not None:
                            if finding['component_version'] is not None:
                                components.add('    ' + finding['component_name']+' v'+finding['component_version'])
                            else:
                                components.add('    ' + finding['component_name'])
                    if components:
                        print('\nVulnerable components:')
                        for component in sorted(components):
                            print(component)

                    # Print link to the list of findings on DefectDojo
                    if args['product_id'] is not None: # If a product id was passed
                        # Print link specific for that product
                        findings_list_url = response.request.url.replace('api/v2/findings/', 'product/'+args['product_id']+'/finding/all') # Mount URL using the previous API call as base
                        findings_list_url = re.sub('test__engagement__product=\d+&?', '', findings_list_url)
                        findings_list_url = re.sub('limit=\d+&?', '', findings_list_url)
                        findings_list_url = re.sub('%0A', '', findings_list_url)
                        print('\n\nYou can also view this list on DefectDojo:\n'+findings_list_url) # Print URL
                    else:
                        # Print general link
                        findings_list_url = response.request.url.replace('api/v2/findings/', 'finding') # Mount URL using the previous API call as base
                        print('\n\nYou can also view this list on DefectDojo:\n'+findings_list_url) # Print URL

                    # Print findings using tabulate (https://pypi.org/project/tabulate)
                    table = dict()
                    table['Severity'] = list()
                    table['Title'] = list()
                    table['URL'] = list()
                    for finding in json_out['results']:
                        table['Severity'].append(finding['severity'])
                        if len(finding['title']) <= 70: # Truncate title bigger then 70 chars
                            table['Title'].append(finding['title'])
                        else:
                            table['Title'].append(finding['title'][:70]+'...')
                        table['URL'].append(args['url']+'/finding/'+str(finding['id']))
                    print(tabulate(table, headers='keys', tablefmt='fancy_grid'))

                    # Exit
                    if args['fail_if_found'] != 'NULL': # If --fail_if_found flag was passed

                        findings_sev = set(table['Severity'])
                        # Get maximum severity from listed findings
                        if 'Info' in findings_sev:
                            sev_max = 1
                        if 'Low' in findings_sev:
                            sev_max = 2
                        if 'Medium' in findings_sev:
                            sev_max = 3
                        if 'High' in findings_sev:
                            sev_max = 4
                        if 'Critical' in findings_sev:
                            sev_max = 5

                        # Parse fail_if_found flag
                        if args['fail_if_found'] == 'Info':
                            fail_if_found = 1
                        if args['fail_if_found'] == 'Low':
                            fail_if_found = 2
                        if args['fail_if_found'] == 'Medium':
                            fail_if_found = 3
                        if args['fail_if_found'] == 'High':
                            fail_if_found = 4
                        if args['fail_if_found'] == 'Critical':
                            fail_if_found = 5

                        if sev_max >= fail_if_found:
                            exit(1)
                        else:
                            exit(0)

                else:
                    exit(0)
        else: # Failure
            # Pretty print output in json
            pretty_json_out = json.dumps(json_out, indent=4)
            print(pretty_json_out)
            exit(1)

    def update(self, url, api_key, finding_id, active=None, mitigated=None, **kwargs):
        # Prepare JSON data to be send
        request_json = dict()
        API_URL = url+'/api/v2'
        FINDINGS_URL = API_URL+'/findings/'
        FINDINGS_ID_URL = FINDINGS_URL+str(finding_id)+'/'
        if active is not None:
            request_json['active'] = active
        if mitigated is not None:
            request_json['is_Mitigated'] = mitigated
        request_json = json.dumps(request_json)

        # Make the request
        response = Util().request_apiv2('PATCH', FINDINGS_ID_URL, api_key, data=request_json)
        return response

    def _update(self):
        # Read user-supplied arguments
        parser = argparse.ArgumentParser(description='Update a finding on DefectDojo',
                                         usage='defectdojo finding update FINDING_ID [<args>]')
        optional = parser._action_groups.pop()
        required = parser.add_argument_group('required arguments')
        parser.add_argument('finding_id', help='ID of the finding to be updated')
        required.add_argument('--url', help='DefectDojo URL', required=True)
        required.add_argument('--api_key', help='API v2 Key', required=True)
        optional.add_argument('--active', help='Set finding as active (true) or inactive (false)',
                              choices=['true', 'false'])
        optional.add_argument('--mitigated', help='Indicates if the finding is mitigated (true) or not (false)',
                              choices=['true', 'false'])
        parser._action_groups.append(optional)
        # Parse out arguments ignoring the first three (because we're inside a sub_command)
        args = vars(parser.parse_args(sys.argv[3:]))

        # Adjust args
        if args['active'] is not None:
            if args['active'] == 'true':
                args['active'] = True
            else:
                args['active'] = False
        if args['mitigated'] is not None:
            if args['mitigated'] == 'true':
                args['mitigated'] = True
            else:
                args['mitigated'] = False

        # Update finding
        response = self.update(**args)

        # Pretty print JSON response
        Util().default_output(response, sucess_status_code=200)

    def close(self, url, api_key, finding_id, **kwargs):
        # Prepare parameters
        request_params = dict()
        request_params['url'] = url
        request_params['api_key'] = api_key
        request_params['finding_id'] = finding_id
        request_params['active'] = False
        request_params['mitigated'] = True

        # Call the update method with active=False and mitigated=True
        response = self.update(**request_params)
        return response

    def _close(self):
        # Read user-supplied arguments
        parser = argparse.ArgumentParser(description='Close a finding on DefectDojo',
                                         usage='defectdojo finding close FINDING_ID [<args>]')
        required = parser.add_argument_group('required arguments')
        parser.add_argument('finding_id', help='ID of the finding to be closed')
        required.add_argument('--url', help='DefectDojo URL', required=True)
        required.add_argument('--api_key', help='API v2 Key', required=True)
        # Parse out arguments ignoring the first three (because we're inside a sub_command)
        args = vars(parser.parse_args(sys.argv[3:]))

        # Close finding
        response = self.close(**args)

        # Pretty print JSON response
        Util().default_output(response, sucess_status_code=200)

    def add_note(self, url, api_key, finding_id, entry, private=None, note_type=None, **kwargs):
        # Prepare parameters
        API_URL = url+'/api/v2/'
        FINDINGS_URL = API_URL+'findings/'
        FINDINGS_ID_URL = FINDINGS_URL+str(finding_id)+'/'
        FINDINGS_ID_NOTES_URL = FINDINGS_ID_URL+'notes/'

        # Prepare JSON data to be send
        request_json = dict()
        request_json['entry'] = entry
        if private is not None:
            request_json['private'] = private
        if note_type is not None:
            request_json['note_type'] = note_type
        request_json = json.dumps(request_json)

        # Make the request
        response = Util().request_apiv2('POST', FINDINGS_ID_NOTES_URL, api_key, data=request_json)
        return response

    def list_multiple_test_types(self, url, api_key, test_types, **kwargs):
        # Create parameters to be requested
        request_params = kwargs
        API_URL = url+'/api/v2'
        FINDINGS_URL = API_URL+'/findings/'

        # Get list of json responses
        json_out_list = list()
        for test_type in test_types:
            request_params['test__test_type'] = test_type
            response = Util().request_apiv2('GET', FINDINGS_URL, api_key, params=request_params)
            json_out_list.append(json.loads(response.text))

        # Merge responses
        json_out_result = dict()
        json_out_result['count'] = 0
        json_out_result['results'] = list()
        for json_out in json_out_list:
            for finding in json_out['results']:
                json_out_result['count'] += 1
                json_out_result['results'].append(finding)

        # Make a request passing the list of test_types so that the url at the tool output works properly
        request_params['test__test_type'] = test_types
        response = Util().request_apiv2('GET', FINDINGS_URL, api_key, params=request_params)
        # Replace the response body with the one we created
        type(response).text = PropertyMock(return_value=json.dumps(json_out_result))
        return response
