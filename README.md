# Readability Exporter
*A tiny tool that helps you export your Readability bookmarks through the 
Readability Reader API.*

This little script takes credentials for a Readability account and the 
API key and secret to create the standard Readability export file in 
JSON format that can be used to **import your links into 
[Instapaper](https://www.instapaper.com/)**. 

The script can also create a bookmarks.html export file in the del.icio.us 
flavour including tags to allow direct **import into 
[Pocket](https://getpocket.com/)** (unfortunately, Pocket does not order the 
links by the date provided in the file, so it can screw up your reading list). 

As a bonus, the script can also create a raw dump including all the additional 
details the Readability Reader API provides for every single bookmark.

We think about adding support for Python 2, as that could also be useful for 
some, currently I have only tested the script on Python 3.4. Another idea is 
to support an input file, the raw data dump you can generate with this script. 
Then this script could be used to generate various output formats for different 
imports even after Readability has shut down its bookmarking service on 
30 Sep 2016.

## Background
When I heard in August 2016, that Readability will shutdown its bookmarking 
and read-it-later service, I was trying to export all my data, but the email 
with the link to the export file never arrived at my inbox. I repeated the 
procedure on the [Tools](https://readability.com/tools/) page a couple of 
times and waited for weeks without getting anything.

So about ten days before the service will shut down, I decided to look at the 
Readability Developer API to see if I could perhaps export my data myself. 
Luckily, this proved to be an easy exercise.

And I thought that if my little export script works for my 4.000 bookmarks, 
why should it not work for others? So I decided to publish this tiny tool 
to allow others exporting their Readability bookmarks without having to 
write their own script. 

**Use at your own risk - it worked perfectly for me.** 

## Installation
Grab a copy of the script with Git 
(`git clone https://github.com/goetzb/readability-exporter.git`) or download the 
script from [https://github.com/goetzb/readability-exporter](https://github.com/goetzb/readability-exporter)

To run the script, you need to install the requirements from `requirements.txt` - 
best in a new Python 3 virtual environment:
```shell
pip install -r /path/to/requirements.txt
```

You can also install the two direct dependencies manually with:
```shell
pip install click
pip install readability-api
```

The script uses the [Readability Python API](https://readability-python-library.readthedocs.io/en/latest/index.html) 
to access the [Readability Reader API](https://www.readability.com/developers/api/reader). 

To make creating the command line interface a bit easier, I am using [Click](http://click.pocoo.org/6/) .

## Setup
After you have installed all dependencies (Python 3, Click, Readability Python 
API), you need to tell the script what API key, API secret and login 
credentials it should use to connect to the Readability Reader API.

The first thing I needed to do was to generate Readability API keys in the 
[Readability account settings](https://readability.com/settings/account). This 
is a quick and easy process and only takes seconds! 

My preferred way to let the script know about my API and login credentials is 
to set the relevant environment variables: 
```shell
$ export READABILITY_CONSUMER_KEY="{your Reader API key}"
$ export READABILITY_CONSUMER_SECRET="{your Reader API secret}"
$ export READABILITY_USERNAME="{your username}"
$ export READABILITY_PASSWORD="{your password}"
```

But you can also specify the key, secret, username and password directly when 
you call the script.

## Usage
Once you have installed all dependencies and have your Readability Reader API 
and login details ready, the simplest usage is:
```shell
$ python readability-exporter.py --format json
```

Yes, that's all you have to do to test the export and get the 15 newest 
bookmarks you have saved to Readability.

You can flexibly export as many bookmarks in one go as you like by using the 
`--bookmarks` option:
```shell
$ python readability-exporter.py --format json --bookmarks 100
```
 
This  will export the newest 100 bookmarks you saved in the default 
Readability JSON format. 

Of course, if you want to export everything, but you do not know how many 
bookmarks you actually have saved, we also have you covered, simply specify 
`--bookmarks 0`:
```shell
$ python readability-exporter.py --format json --bookmarks 0
```

If you not only want the default export file Readability used to provide, you 
can also add `--format html` to get a bookmarks.html export including tags, 
just like what you can download from del.icio.us. 
And if you add `--format jsonraw` you can generate an output file that includes 
all data the Readability Reader API provides: 
```shell
$ python readability-exporter.py --format json --format html --format jsonraw --bookmarks 0
```

To make it easier for you to locate the file after the export, we try to open 
your file manager and select your file. If you do not like this behaviour, 
simply turn it off with `--not_show_file`:
```shell
$ python readability-exporter.py --format json --bookmarks 100 --not_show_file
```

If you want to provide your API key, secret and your login details directly, 
you can do so using the `--api_key`, `--api_secret`, `--login_user` and 
`--login_pw` options:
```shell
$ python readability-exporter.py --api_key "{your API key}" --api_secret "{your API secret}" --login_user  "{your Readability username}" --login_pw "{your readability password}" --format json
```

There are a few more options available, for example to specify where you want 
the export file to be saved or what filename it should have. You can find out 
 more about all the options with the `--help` option:
```shell
$ python readability-exporter.py --help
```

## Licensing
The code for `readability-exporter` is licensed under the 
[MIT License](http://opensource.org/licenses/MIT).