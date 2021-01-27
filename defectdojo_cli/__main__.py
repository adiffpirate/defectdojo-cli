#!/bin/python3

import sys
import argparse
from defectdojo_cli import Findings
from defectdojo_cli import Engagements

# Multilevel argparse based on https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html
class DefectDojoCLI:
    def __init__(self):
        parser = argparse.ArgumentParser(
                description='CI/CD integration for DefectDojo',
                usage='''defect-dojo <command> [<args>]

    You can use the following commands:
            findings        Operations related to findings (findings --help for more details)
            engagements     Operations related to engagements (engagements --help for more details)
        ''')
        parser.add_argument('command', help='Command to run')
        # Parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print('Unrecognized command')
            parser.print_help()
            exit(1)
        # Use dispatch pattern to invoke method with same name
        getattr(self, args.command)()

    def findings(self):
        Findings()

    def engagements(self):
        Engagements()

if __name__ == '__main__':
    DefectDojoCLI()
