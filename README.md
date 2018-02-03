## `teller` - a command-line bank teller
This open-source bank teller can be used to access your bank balances in [Sbanken](https://sbanken.no) using [their open APIs](https://utvikler.sbanken.no/).

### Running the program
#### Prerequisites
 - You must have [Python 2.x](https://www.python.org/) installed
 - You must have enabled "beta" access in Sbanken at [https://secure.sbanken.no/Home/Settings/BetaProgram](https://secure.sbanken.no/Home/Settings/BetaProgram) and created an application at [https://secure.sbanken.no/Personal/ApiBeta/Info](https://secure.sbanken.no/Personal/ApiBeta/Info).
#### Complete installation
You can download the script using `git clone`:  
`git clone https://github.com/roys/python-cli-teller.git`

You then might need to download a couple of Python libraries:
`cd python-cli-teller`  
`pip install --user -r requirements.txt` (remove `--user` to do a global installation of the libs)  

