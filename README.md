# `teller` - a command-line bank teller
This open-source bank teller can be used to access your bank balances in [Sbanken](https://sbanken.no) using [their open APIs](https://utvikler.sbanken.no/).

<img src="https://github.com/roys/python-cli-teller/raw/master/misc/screenshots/teller.png" width="640"/>

## Features
 - See your account balances
 - Transfer money between your own accounts
 - List and see totals of your transactions
 - Search in your transactions

## Video demo
[![YouTube demo of bank teller](https://img.youtube.com/vi/E34x4dx_Ezo/0.jpg)](https://youtu.be/E34x4dx_Ezo)

## Getting started
### Prerequisites
 - You must have [Python 2.x](https://www.python.org/) installed
 - You must be a customer of Sbanken have enabled "beta" access at [https://secure.sbanken.no/Home/Settings/BetaProgram](https://secure.sbanken.no/Home/Settings/BetaProgram) and created an application at [https://secure.sbanken.no/Personal/ApiBeta/Info](https://secure.sbanken.no/Personal/ApiBeta/Info).
### Complete installation
You can download the script using `git clone`:  
`git clone https://github.com/roys/python-cli-teller.git`

You then might need to download a couple of Python libraries:  
`cd python-cli-teller`  
`pip install --user -r requirements.txt` (remove `--user` to do a global installation of the libs)  

If you want to be able to just type `teller` in any directory instead of having to type `python teller.py` you can create a shortcut:  
`chmod +x teller.py`  
`ln -s $(pwd)/teller.py /usr/local/bin/teller`

### Initial setup
If you didn't create the shortcut in the last example you have to type `python teller.py`. Otherwise:  
`teller`

You will now be asked for the client ID, client secret and your user id. The user ID is your social security number.

If you want to run `teller` without having to enter all those credentials you can choose your own password that only you will know. If you do that the password will be used as the key to encrypt the data you entered + a more temporarily access token that Sbanken's service returns.

## Running the program
You can print the help using `teller -h` or `teller --help`. To get help for one specifc command you can type `teller {comand} -h`, e.g. `teller trans -h`.

### List balances 💵
Listing the balances is the default command (and an alias of typing `teller accounts`):  
`teller`

### Transfer money ↔️
To transfer money between your accounts you just type as follows:  
`teller transfer {from account number/name/position} {to account number/name/position} {amount} [message]`

The account "position" is the position that is printed in the left column when doing the command `teller`. You don't have to match the casing if using the account name. You can mix between using account name, account number and account positions as desired.

The message is optional. If you have a message with several words you need to use an apostrophe (') or quotation mark (") in the start and end of the message.

### List transactions 📃
To list the transactions for the last 30 days you just type:  
`teller trans {account number/name/position}`

The account "position" is the position that is printed in the left column when doing the command `teller`. You don't have to match the casing if using the account name.

You can also specify a start date of the the transaction and an optional end date. If there are more than 1000 transactions you can page the data as well:  
`teller trans {account} [start] [end] [index] [quantity]`

The date format is relatively forgiving, so you can choose between typing e.g. `1 july 2017` and `2017-07-01`.

### Search transactions 🔍
This is a pretty neat function. Be sure to read about all the other options for listing transactions. In addition to the listing `teller` can do a local search from the data returned and only show those and the sum of those.

To e.g. sum up all interests for the year 2017 you could write as follows:  
`teller trans -s kreditrenter brukskonto "1 jan 2017" "31 dec 2017"`

### Changing the language 🇬🇧 🇺🇸 🇳🇴
The script has language support for English and Norwegian. English is default, but it's very easy to change the preferred language:  
`teller -l {no|en}`

The language strings can be found in the `strings_*.ini` files.
