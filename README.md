# o365_ip
Pull IP addresses from Microsoft Office 365 periodically

# usage

## Quick Start

    python3 ./o365_ip.py -d delta.json

This is bascially the command you always want to run. It will pull the latest from Microsoft and generate a json file that indicates which IPs are new and which are removed since the last run.

If this is your first run, it will put the entire content in the "add" list.

Note the script defaults to the `Worldwide` o365 instance list.

Add `-D` for some more context as to what is happening

## Full Help

    python3 ./o365_ip.py -h
    usage: o365_ip.py [-h] [-D, --debug] [-f, --force] [-o, --outfile OUTFILE]
                    [-v, --verfile VERFILE] [-d, --deltafile DELTAFILE]
                    [-g, --guidfile GUIDFILE]
                    [-i, --instance {Worldwide,China,Germany,USGovDoD,USGovGCCHigh}]
                    [-p, --disable_optional_ips]

    Get Microsoft Office 365 IP lists.

    optional arguments:
    -h, --help            show this help message and exit
    -D, --debug           Full download output
    -f, --force           Download update even if version has not changed
    -o, --outfile OUTFILE
                            Full download output
    -v, --verfile VERFILE
                            File to store version infomation
    -d, --deltafile DELTAFILE
                            Generate delta to file
    -g, --guidfile GUIDFILE
                            File to load guid from. Will generate if file not
                            found
    -i, --instance {Worldwide,China,Germany,USGovDoD,USGovGCCHigh}
                            Microsoft Office 365 Instance
    -p, --disable_optional_ips
                            Do not include optional IPs