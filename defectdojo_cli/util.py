from datetime import datetime
import json
import requests

class Util(object):
    def __init__(self):
        self.ACCEPTED_SCANS = ['Netsparker Scan', 'Burp Scan', 'Nessus Scan', 'Nmap Scan', 'Nexpose Scan',
                               'AppSpider Scan', 'Veracode Scan', 'Checkmarx Scan', 'Checkmarx Scan detailed',
                               'Crashtest Security JSON File', 'Crashtest Security XML File', 'ZAP Scan',
                               'Arachni Scan', 'VCG Scan', 'Dependency Check Scan',
                               'Dependency Track Finding Packaging Format (FPF) Export', 'Retire.js Scan',
                               'Node Security Platform Scan', 'NPM Audit Scan', 'Qualys Scan',
                               'Qualys Infrastructure Scan (WebGUI XML)', 'Qualys Webapp Scan', 'OpenVAS CSV',
                               'Snyk Scan', 'Generic Findings Import', 'Trustwave Scan (CSV)', 'SKF Scan',
                               'Clair Klar Scan', 'Bandit Scan', 'ESLint Scan', 'SSL Labs Scan', 'Acunetix Scan',
                               'Fortify Scan', 'Gosec Scanner', 'SonarQube Scan', 'SonarQube Scan detailed',
                               'SonarQube API Import', 'MobSF Scan', 'Trufflehog Scan', 'Nikto Scan', 'Clair Scan',
                               'Brakeman Scan', 'SpotBugs Scan', 'AWS Scout2 Scan', 'AWS Prowler Scan',
                               'IBM AppScan DAST', 'PHP Security Audit v2', 'PHP Symfony Security Check',
                               'Safety Scan', 'DawnScanner Scan', 'Anchore Engine Scan', 'Bundler-Audit Scan',
                               'Twistlock Image Scan', 'Kiuwan Scan', 'Blackduck Hub Scan',
                               'Blackduck Component Risk', 'Openscap Vulnerability Scan', 'Wapiti Scan',
                               'Immuniweb Scan', 'Sonatype Application Scan', 'Cobalt.io Scan',
                               'Mozilla Observatory Scan', 'Whitesource Scan', 'Contrast Scan',
                               'Microfocus Webinspect Scan', 'Wpscan', 'Sslscan', 'JFrog Xray Scan', 'Sslyze Scan',
                               'SSLyze 3 Scan (JSON)', 'Testssl Scan', 'Hadolint Dockerfile check', 'Aqua Scan',
                               'HackerOne Cases', 'Xanitizer Scan', 'Outpost24 Scan', 'Burp Enterprise Scan',
                               'DSOP Scan', 'Trivy Scan', 'Anchore Enterprise Policy Check', 'Gitleaks Scan',
                               'Choctaw Hog Scan', 'Harbor Vulnerability Scan', 'Github Vulnerability Scan',
                               'Yarn Audit Scan', 'BugCrowd Scan', 'GitLab SAST Report', 'AWS Security Hub Scan',
                               'GitLab Dependency Scanning Report', 'HuskyCI Report', 'Semgrep JSON Report',
                               'Risk Recon API Importer', 'DrHeader JSON Importer', 'Checkov Scan',
                               'kube-bench Scan', 'CCVS Report', 'ORT evaluated model Importer', 'SARIF']
        self.ACCEPTED_SCANS = sorted(self.ACCEPTED_SCANS, key=lambda s: s.lower()) # Case insentitive sorting

    # Generic method for all HTTP requests
    # IMPORTANT: The url must end with '/', otherwise some requests will not work
    def request_apiv2(self, http_method, url, api_key, params=dict(), data=None, files=None, verify=False):
        headers = dict()
        headers['Authorization'] = 'Token '+api_key
        if not files:
            headers['Accept'] = 'application/json'
            headers['Content-Type'] = 'application/json'

        response = requests.request(method=http_method, url=url, params=params, data=data,
                                    files=files, headers=headers, verify=verify)
        return response

    # Pretty print JSON response exiting with a sucess if the response status code is the same as the 'sucess_status_code' argument
    def default_output(self, response, sucess_status_code):
        json_out = json.loads(response.text)
        pretty_json_out = json.dumps(json_out, indent=4)
        print(pretty_json_out)

        if response.status_code == sucess_status_code: # Sucess
            exit(0)
        else: # Failure
            exit(1)
