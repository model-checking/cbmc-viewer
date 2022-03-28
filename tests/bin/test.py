import re
import sys

def viewer_options_without_reportdir(viewer_command):
    """Strip --reportdir from command line options used to invoke viewer."""

    command = re.sub(r'\s+', ' ', viewer_command.strip())

    # strip path used to invoke viewer from front of command
    options = command.split(' ', 1)[-1]
    # strip --reportdir option from within command
    options = re.sub(r'--reportdir\s+[^\s]+', '', options)

    return re.sub(r'\s+', ' ', options.strip())

def main():
    cmd = ' '.join(sys.argv[1:])
    print()
    print(viewer_options_without_reportdir(cmd))
    print()

if __name__ == "__main__":
    main()
