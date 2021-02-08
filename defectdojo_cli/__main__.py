import sys
import argparse
from defectdojo_cli import Findings
from defectdojo_cli import Engagements

# Multilevel argparse based on https://chase-seibert.github.io/blog/2014/03/21/python-multilevel-argparse.html
class DefectDojoCLI(object):
    def parse_cli_args(self):
        parser = argparse.ArgumentParser(
                description='CLI wrapper for DefectDojo using APIv2',
                usage='''defectdojo <command> [<args>]

    You can use the following commands:
            findings        Operations related to findings (findings --help for more details)
            engagements     Operations related to engagements (engagements --help for more details)
        ''')
        parser.add_argument('command', help='Command to run', choices=['findings', 'engagements'])
        # Parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        # Use dispatch pattern to invoke method with same name (that starts with _)
        getattr(self, '_'+args.command)()

    def _findings(self):
        Findings().parse_cli_args()

    def _engagements(self):
        Engagements().parse_cli_args()

def main():
    DefectDojoCLI().parse_cli_args()

if __name__ == '__main__':
    main()
