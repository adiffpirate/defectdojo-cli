from datetime import datetime
import json
import sys
import argparse
import requests

ACCEPTED_SCANS = ['Netsparker Scan', 'Burp Scan', 'Nessus Scan', 'Nmap Scan', 'Nexpose Scan', 'AppSpider Scan',
                  'Veracode Scan', 'Checkmarx Scan', 'Checkmarx Scan detailed', 'Crashtest Security JSON File',
                  'Crashtest Security XML File', 'ZAP Scan', 'Arachni Scan', 'VCG Scan',
                  'Dependency Check Scan', 'Dependency Track Finding Packaging Format (FPF) Export',
                  'Retire.js Scan', 'Node Security Platform Scan', 'NPM Audit Scan', 'Qualys Scan',
                  'Qualys Infrastructure Scan (WebGUI XML)', 'Qualys Webapp Scan', 'OpenVAS CSV', 'Snyk Scan',
                  'Generic Findings Import', 'Trustwave Scan (CSV)', 'SKF Scan', 'Clair Klar Scan',
                  'Bandit Scan', 'ESLint Scan', 'SSL Labs Scan', 'Acunetix Scan', 'Fortify Scan',
                  'Gosec Scanner', 'SonarQube Scan', 'SonarQube Scan detailed', 'SonarQube API Import',
                  'MobSF Scan', 'Trufflehog Scan', 'Nikto Scan', 'Clair Scan', 'Brakeman Scan', 'SpotBugs Scan',
                  'AWS Scout2 Scan', 'AWS Prowler Scan', 'IBM AppScan DAST', 'PHP Security Audit v2',
                  'PHP Symfony Security Check', 'Safety Scan', 'DawnScanner Scan', 'Anchore Engine Scan',
                  'Bundler-Audit Scan', 'Twistlock Image Scan', 'Kiuwan Scan', 'Blackduck Hub Scan',
                  'Blackduck Component Risk', 'Openscap Vulnerability Scan', 'Wapiti Scan', 'Immuniweb Scan',
                  'Sonatype Application Scan', 'Cobalt.io Scan', 'Mozilla Observatory Scan', 'Whitesource Scan',
                  'Contrast Scan', 'Microfocus Webinspect Scan', 'Wpscan', 'Sslscan', 'JFrog Xray Scan',
                  'Sslyze Scan', 'SSLyze 3 Scan (JSON)', 'Testssl Scan', 'Hadolint Dockerfile check',
                  'Aqua Scan', 'HackerOne Cases', 'Xanitizer Scan', 'Outpost24 Scan', 'Burp Enterprise Scan',
                  'DSOP Scan', 'Trivy Scan', 'Anchore Enterprise Policy Check', 'Gitleaks Scan',
                  'Choctaw Hog Scan', 'Harbor Vulnerability Scan', 'Github Vulnerability Scan',
                  'Yarn Audit Scan', 'BugCrowd Scan', 'GitLab SAST Report', 'AWS Security Hub Scan',
                  'GitLab Dependency Scanning Report', 'HuskyCI Report', 'Semgrep JSON Report',
                  'Risk Recon API Importer', 'DrHeader JSON Importer', 'Checkov Scan', 'kube-bench Scan',
                  'CCVS Report', 'ORT evaluated model Importer', 'SARIF']

class Findings(object):
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Perform <sub_command> related to findings on DefectDojo',
            usage='''defect-dojo findings <sub_command> [<args>]

    You can use the following sub_commands:
        upload      Upload findings (scan results) to DefectDojo
''')
        parser.add_argument('sub_command', help='Sub_command to run')
        args = parser.parse_args(sys.argv[2:3]) # Get sub_command
        if not hasattr(self, args.sub_command):
            print('Unrecognized sub_command')
            parser.print_help()
            exit(1)
        # Use dispatch pattern to invoke method with same name
        getattr(self, args.sub_command)()

    def upload(self):
        parser = argparse.ArgumentParser(description='Upload findings (scan results) to DefectDojo',
                                         usage='defect-dojo findings upload RESULT_FILE [<args>]')
        parser.add_argument('result_file', help='File with the results to be uploaded')
        required = parser.add_argument_group('required arguments')
        required.add_argument('--scanner', help='Type of scanner', required=True, choices=ACCEPTED_SCANS)
        required.add_argument('--url', help='DefectDojo URL', required=True)
        required.add_argument('--api_key', help='API v2 Key', required=True)
        required.add_argument('--engagement_id', help='Engagement ID', required=True)
        required.add_argument('--lead_id', help='ID of the user conducting the operation', required=True)
        parser.add_argument('--active', help='Mark vulnerabilities found as active (default)',
                          action='store_true', dest='active')
        parser.add_argument('--inactive', help='Mark vulnerabilities found as inactive',
                          action='store_false', dest='active')
        parser.set_defaults(active=True)
        parser.add_argument('--min_severity', help='Ignore findings below this severity (default = "Low")',
                          choices=['Informational', 'Low', 'Medium', 'High', 'Critical'])
        parser.add_argument('--tag', help='Scanner tag (can be used multiple times)', action='append')

        # Parse out arguments ignoring the first three (because we're inside a sub-command)
        args = vars(parser.parse_args(sys.argv[3:]))
        self.result_file = args['result_file']
        self.scanner = args['scanner']
        self.url = args['url']
        self.api_key = args['api_key']
        self.engagement_id = args['engagement_id']
        self.lead_id = args['lead_id']
        self.active = args['active']
        self.min_severity = args['min_severity']
        if args['tag'] is not None:
            self.tags = args['tag']

        API_URL = self.url+'/api/v2'
        IMPORT_SCAN_URL = API_URL+'/import-scan/'
        AUTH_TOKEN = 'Token '+self.api_key

        headers = dict()
        request_json = dict()
        files = dict()

        # Prepare headers
        headers['Authorization'] = AUTH_TOKEN

        # Prepare JSON data to send to API
        request_json['minimum_severity'] = 'Low'
        request_json['scan_date'] = datetime.now().strftime('%Y-%m-%d')
        request_json['scan_type'] = self.scanner
        request_json['verified'] = False
        request_json['engagement'] = self.engagement_id
        request_json['lead'] = self.lead_id
        request_json['active'] = self.active
        request_json['minimum_severity'] = self.min_severity
        if args['tag'] is not None:
            request_json['tags'] = self.tags

        # Prepare file data to send to API
        files['file'] = open(self.result_file)

        # Make a request to API
        response = requests.post(IMPORT_SCAN_URL, headers=headers, files=files, data=request_json)
        self.output = json.loads(response.text)
        self.pretty_output = json.dumps(self.output, indent=4)
        print(self.pretty_output)

        if response.status_code == 201:
            # Sucess
            exit(0)
        else:
            # Failure
            exit(1)

    def list(self):
        parser = argparse.ArgumentParser(description='List findings stored on DefectDojo',
                                         usage='defect-dojo findings list [<args>]')
        required = parser.add_argument_group('required arguments')
        required.add_argument('--url', help='DefectDojo URL', required=True)
        required.add_argument('--api_key', help='API v2 Key', required=True)
        parser.add_argument('--id', help='Get finding with this id')
        parser.add_argument('--product_id', help='Filter by product')
        parser.add_argument('--engagement_id', help='Filter by engagement')
        parser.add_argument('--scanner', help='Filter by scanner', choices=ACCEPTED_SCANS)
        parser.add_argument('--active', help='List only actives findings',
                            action='store_true', dest='active')
        parser.add_argument('--inactive', help='List only inactives findings',
                            action='store_false', dest='active')
        parser.add_argument('--valid', help='List only valid findings (true-positives)',
                            action='store_true', dest='valid')
        parser.add_argument('--false_positives', help='List only false_positives findings',
                            action='store_false', dest='valid')
        parser.add_argument('--in_scope', help='List only findings in-scope',
                            action='store_true', dest='scope')
        parser.add_argument('--out_of_scope', help='List only findings out-of-scope',
                            action='store_false', dest='scope')
        parser.add_argument('--json', help='Print output in JSON format')
        parser.set_defaults(active=None, valid=None, scope=None)

        request_params = dict()
        headers = dict()
        # Parse out arguments ignoring the first three (because we're inside a sub-command)
        args = vars(parser.parse_args(sys.argv[3:]))

        # Parse url and api_key
        self.url = args['url']
        self.api_key = args['api_key']
        API_URL = self.url+'/api/v2'
        FINDINGS_URL = API_URL+'/findings/'
        AUTH_TOKEN = 'Token '+self.api_key
        # Prepare headers
        headers['Authorization'] = AUTH_TOKEN

        if args['id'] is not None:
            self.id = args['id']
            request_params['id'] = self.id
        if args['product_id'] is not None:
            self.product_id = args['product_id']
            request_params['test__engagement__product'] = self.product_id
        if args['engagement_id'] is not None:
            self.engagement_id = args['engagement_id']
            request_params['test__engagement'] = self.engagement_id
        if args['scanner'] is not None:
            self.scanner = args['scanner']
            # In order to filter scanner we need to get its ID via API
            temp_params = dict()
            temp_params['name'] = self.scanner
            # Make a get request to test_types passing the scanner as parameter
            temp_response = requests.get(API_URL+'/test_types', headers=headers, params=temp_params)
            # Tranform the above response in json and get the id
            self.scanner_id = json.loads(temp_response.text)['results'][0]['id']
            # Add to request_params
            request_params['test__test_type'] = self.scanner_id
        if args['active'] is not None:
            self.active = args['active']
            if self.active is True:
                request_params['active'] = 2
            if self.active is False:
                request_params['active'] = 3
        if args['valid'] is not None:
            self.valid = args['valid']
            if self.valid is True:
                request_params['false_p'] = 3
            if self.valid is False:
                request_params['false_p'] = 2
        if args['scope'] is not None:
            self.scope = args['scope']
            if self.scope is True:
                request_params['out_of_scope'] = 3
            if self.scope is False:
                request_params['out_of_scope'] = 2

        # Make a request to API
        response = requests.get(FINDINGS_URL, headers=headers, params=request_params)

        self.json_out = json.loads(response.text)
        if args['json'] is not None:
            # Print output in json
            self.pretty_json_out = json.dumps(self.output, indent=4)
            print(self.pretty_json_out)
        else:
            # Print output in a more human readable way
            criticals = []
            highs = []
            mediums = []
            lows = []
            infos = []

            for finding in self.json_out['results']:
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
                print('CRITICAL:')
                for finding in criticals:
                    print(str(finding['title']+': '+self.url+'/finding/'+str(finding['id'])))
                print()
            if highs:
                print('HIGH:')
                for finding in highs:
                    print(str(finding['title']+': '+self.url+'/finding/'+str(finding['id'])))
                print()
            if mediums:
                print('MEDIUM:')
                for finding in mediums:
                    print(str(finding['title']+': '+self.url+'/finding/'+str(finding['id'])))
                print()
            if lows:
                print('LOW:')
                for finding in lows:
                    print(str(finding['title']+': '+self.url+'/finding/'+str(finding['id'])))
                print()
            if infos:
                print('INFO:')
                for finding in infos:
                    print(str(finding['title']+': '+self.url+'/finding/'+str(finding['id'])))
                print()

        if response.status_code == 200:
            # Sucess
            exit(0)
        else:
            # Failure
            exit(1)
