## `teller` - a command-line bank teller
This open-source bank teller can be used to access your bank balances in [Sbanken](https://sbanken.no) using [their open APIs](https://utvikler.sbanken.no/).

### Running the program
#### Prerequisites
 - You must have [Python 2.x](https://www.python.org/) installed
 - You must be a customer of Sbanken have enabled "beta" access at [https://secure.sbanken.no/Home/Settings/BetaProgram](https://secure.sbanken.no/Home/Settings/BetaProgram) and created an application at [https://secure.sbanken.no/Personal/ApiBeta/Info](https://secure.sbanken.no/Personal/ApiBeta/Info).
#### Complete installation
You can download the script using `git clone`:  
`git clone https://github.com/roys/python-cli-teller.git`

You then might need to download a couple of Python libraries:  
`cd python-cli-teller`  
`pip install --user -r requirements.txt` (remove `--user` to do a global installation of the libs)  

If you want to be able to just type `teller` in any directory instead of having to type `python teller.py` you can create a shortcut:  
`chmod +x teller.py`
`ln -s $(pwd)/teller.py /usr/local/bin/teller`

#### Initial setup
If you didn't created the shortcut in the last example you have to type `python teller.py`. Otherwise:
`teller`

You will now be asked for the client ID, client secret and your user id. The user ID is your social security number.

If you want to run `teller` without having to enter all those credentials you can choose your own password that only you will know. If you do that the password will be used as the key to encrypt the data you entered + a more temporarily access token that Sbanken's service returns.
