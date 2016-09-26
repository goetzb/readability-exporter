# -*- coding: utf-8 -*-
"""Readability Exporter

A tiny tool that helps you export your Readability bookmarks through the Readability Reader API.
See `the GitHub project page <https://github.com/goetzb/readability-exporter>`_ for more information.
"""
# TODO: Make the script compatible with Python 2.7
# TODO: Add /docs
import click
from readability import auth, ReaderClient

# Python standard library modules
from collections import OrderedDict
from os import path, getcwd
from math import ceil
import json
from datetime import datetime
from time import mktime

CONTEXT_SETTINGS = dict(token_normalize_func=lambda x: x.lower())


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--api_key',    envvar='READABILITY_CONSUMER_KEY',    help='Readability API key')
@click.option('--api_secret', envvar='READABILITY_CONSUMER_SECRET', help='Readability API secret')
@click.option('--login_user', envvar='READABILITY_USERNAME',        help='Readability web login username')
@click.option('--login_pw',   envvar='READABILITY_PASSWORD',        help='Readability web login password')
@click.option('-f', '--format', type=click.Choice(['json', 'html', 'jsonraw']), multiple=True,
              help="""One or more export formats.
To import into Instapaper, use 'json'.
To import into Pocket, use 'html'.
To get all details from the API and transform it yourself into something useful, use 'jsonraw'.
'json' = default Readability export including title, URL, date added, archived and if the link was favourited
'html' = bookmarks.html as exported by del.icio.us including tags
'jsonraw' = raw dump as provided by Readability Reader API""")
@click.option('-b', '--bookmarks', default=15,
              help='Number of bookmarks to export, 0 to export all bookmarks - default 15')
@click.option('-d', '--export_directory',
              type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True, resolve_path=True),
              default=getcwd(),
              help='Where the export files should be saved, defaults to the current working directory')
@click.option('-e', '--export_filename',
              default='readability-export_{timestamp}_{format}.{filetype}',
              help="Naming pattern for export documents, default: 'readability-export_{timestamp}_{format}.{filetype}'")
@click.option('--not_show_file', is_flag=True,
              help='Add this flag if you do not want that the file manager opens automatically after the export')
@click.option('-e', '--http_error_threshold', default=5, help='Number of retries when an error occurs, defaults to 5')
@click.version_option(version='20160926a',
                      prog_name='readability-exporter',
                      message='%(prog)s, version %(version)s by Goetz Buerkle <goetz.buerkle@gmail.com>')
def readability_exporter(api_key, api_secret, login_user, login_pw,
                         format, bookmarks, export_directory, export_filename, not_show_file, http_error_threshold):
    """Readability Exporter
   
   This little script takes credentials for a Readability account and the API key and secret to create the standard
   Readability export file in JSON format that can be used to import your links into Instapaper.
   We think about adding support for the del.icio.us flavour of bookmarks.html to allow direct import into Pocket.
   
   You can find more information about this script on GitHub at https://github.com/goetzb/readability-exporter
   """
    click.echo(click.style('Readability Exporter', bold=True))
    
    # Create string for export filename
    if '{timestamp}' not in export_filename:
        export_filename += '_{timestamp}'
    if '{format}' not in export_filename:
        export_filename += '_{format}'
    if '{filetype}' not in export_filename:
        export_filename += '.{filetype}'

    # Prepare json export dictionary
    export_dict = OrderedDict()
    export_dict['bookmarks'] = []
    # Add empty recommendations list - in my example this was just empty.
    export_dict["recommendations"] = []
    
    # Prepare jsonraw export dictionary
    export_dict_raw = OrderedDict()
    
    # Prepare html export string
    export_html = """<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<!-- This is an automatically generated file.
It will be read and overwritten.
Do Not Edit! -->
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
"""
    
    auth_tokens = get_auth_tokens(api_key=api_key, api_secret=api_secret, login_user=login_user, login_pw=login_pw)
    if len(auth_tokens) != 2:
        click.ClickException("""An error occurred and you could not be authenticated successfully.
Please check your Readability API keys and login details.""")
    
    client = ReaderClient(token_key=auth_tokens[0], token_secret=auth_tokens[1])
    meta_infos = get_readability_meta_infos(readability_reader_client=client)
    click.echo("* You have saved " + click.style("{link_count}".format(
        link_count=meta_infos['bookmarks_total']), bold=True) + " links on Readability")
    
    if bookmarks == 0:
        bookmarks = meta_infos['bookmarks_total']
    
    click.echo("* We are now going to export the latest " + click.style("{export_count}".format(
        export_count=bookmarks), bold=True) + " of your links")
    
    if bookmarks < 50:
        bookmarks_per_page = bookmarks + 1
    else:
        bookmarks_per_page = 50
    bookmarks_get_pages = int(ceil(bookmarks/bookmarks_per_page))

    data_export = export_bookmarks_via_api(readability_reader_client=client,
                                           export_formats=format,
                                           bookmarks_number=bookmarks,
                                           bookmarks_per_page=bookmarks_per_page,
                                           bookmarks_get_pages=bookmarks_get_pages,
                                           export_json=export_dict,
                                           export_html=export_html,
                                           export_jsonraw=export_dict_raw,
                                           error_threshold=http_error_threshold)
    
    click.echo("Bear with us, we are almost there. In the next step we bring the data into the right formats.")

    exported_files = []
    files_export_count = 0
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    with click.progressbar(label='Writing export files...',
                           length=len(format),
                           show_percent=True) as files_bar:
        for export_format in format:
            output_data = data_export[export_format]
            if export_format == 'json' or export_format == 'jsonraw':
                filetype = 'json'
            elif export_format == 'html':
                filetype = 'html'
                output_data += "</DL><p>"
            
            format_export_filename = export_filename.format(timestamp=timestamp,
                                                            format=export_format,
                                                            filetype=filetype)
            
            export_file = write_export_data(filetype=filetype,
                                            directory=export_directory,
                                            filename=format_export_filename,
                                            data=output_data)
            
            exported_files.append(export_file)
            
            files_export_count += 1
            files_bar.update(files_export_count)
    
    # TODO: Improve bookmark count to verify if actually the correct number of bookmarks has been exported
    # Get length of 'bookmarks' in json export dictionary
    click.echo(click.style("Good news! We have successfully exported {number_of_bookmarks} bookmarks for you.".format(
        number_of_bookmarks=bookmarks), fg='green'))

    for exported_file in exported_files:
        if exported_file['file_size'] / 1024 > 1024:
            file_size_string = '{size:d} MiB'.format(size=round(exported_file['file_size'] / 1024 / 1024))
        elif exported_file['file_size'] > 1024:
            file_size_string = '{size:d} KiB'.format(size=round(exported_file['file_size'] / 1024))
        else:
            file_size_string = '{size:d} B'.format(size=exported_file['file_size'])

        click.echo("You can find your exported data in ")
        click.echo(click.style("  {path}".format(path=exported_file['file_path']), bold=True))
        click.echo("  (~{size})".format(size=file_size_string))
    
    click.echo(click.style("Thank you for using this little tool!", reverse=True))
    if not not_show_file:
        click.echo(click.style("We will now try to open your file manager with the exported file selected.",
                               reverse=True))
        click.launch(export_directory, locate=True)


def get_auth_tokens(api_key='', api_secret='', login_user='', login_pw=''):
    """Authentication is based on the auth.xauth() function of the readability-api Python package.
     
     For more details about the authentication, please visit
     https://readability-python-library.readthedocs.io/en/latest/auth.html#client-documentation
     """
    if api_key is '':
        raise click.BadOptionUsage("""Please provide a Readability API key.
You can do this either with --api_key or with the environment variable READABILITY_CONSUMER_KEY.
If you did not create one already, simply visit https://readability.com/settings/account and generate one.
Generating a new Reader API key just takes seconds!""")
    if api_secret is '':
        raise click.BadOptionUsage("""Please provide a Readability API secret.
You can do this either with --api_secret or with the environment variable READABILITY_CONSUMER_SECRET.
If you did not create one already, simply visit https://readability.com/settings/account and generate one.
Generating a new Reader API key just takes seconds!""")
    if login_user is '':
        raise click.BadOptionUsage("""Please provide your Readability user name.
You can do this either with --login_user or with the environment variable READABILITY_USERNAME.""")
    if login_pw is '':
        raise click.BadOptionUsage("""Please provide your Readability password.
You can do this either with --api_pw or with the environment variable READABILITY_PASSWORD.""")
    
    try:
        auth_tokens = auth.xauth(consumer_key=api_key, consumer_secret=api_secret,
                                 username=login_user, password=login_pw)
    except ValueError as e:
        raise click.BadOptionUsage("""Authentication error: {message}
Please check your Readability API key, API secret as well as your login user and login password.
If you did not create one already, simply visit https://readability.com/settings/account and generate one.
Generating a new Reader API key just takes seconds!""".format(message=e))
    
    return auth_tokens


def get_readability_meta_infos(readability_reader_client=None):
    """Query Readability Reader API for basic account information
    
    Return the total number of links the user has saved on Readability in a dictionary.
    """
    bookmarks_meta_response = readability_reader_client.get_bookmarks(per_page=1, page=1)
    bookmarks_response_meta_dict = bookmarks_meta_response.json()
    bookmarks_total = bookmarks_response_meta_dict['meta']['item_count_total']
    
    return {'bookmarks_total': bookmarks_total}


def export_bookmarks_via_api(readability_reader_client=None, bookmarks_number=1, bookmarks_per_page=5,
                             bookmarks_get_pages=1,
                             export_formats=[], export_json=None, export_html=None, export_jsonraw=None,
                             error_threshold=5):
    """Query Readability Reader API to export data

    Return a ordered dictionary with the specified number of links.
    Calculate how many pages we will need to export with the current settings.
    """
    bookmark_export_count = 0
    bookmark_pages_export_count = 0
    error_count = 0
    
    with click.progressbar(label='Exporting links...',
                           length=bookmarks_get_pages,
                           show_percent=True) as bar:
        for tmp_page in range(1, bookmarks_get_pages + 1):
            if bookmark_export_count >= bookmarks_number:
                break
            
            # TODO: Rewrite to take optional input file and read export data from raw API data file
            bookmarks_response = readability_reader_client.get_bookmarks(per_page=bookmarks_per_page, page=tmp_page)
            if bookmarks_response.status_code == 200:
                bookmarks_response_dict = bookmarks_response.json()
                bookmarks = bookmarks_response_dict['bookmarks']
                
                for bookmark in bookmarks:
                    if bookmark_export_count >= bookmarks_number:
                        break
                    
                    # Default Readability json format
                    if 'json' in export_formats:
                        bookmark_dict = OrderedDict()
                        bookmark_dict["article__excerpt"] = bookmark['article']['excerpt']
                        bookmark_dict["favorite"] = bookmark['favorite']
                        if bookmark["date_archived"] is not None:
                            bookmark_dict["date_archived"] = bookmark['date_archived'].replace(" ", "T")
                        else:
                            bookmark_dict["date_archived"] = bookmark["date_archived"]
                        bookmark_dict["article__url"] = bookmark["article"]["url"]
                        if bookmark["date_added"] is not None:
                            bookmark_dict["date_added"] = bookmark["date_added"].replace(" ", "T")
                        else:
                            bookmark_dict["date_added"] = bookmark["date_added"]
                        if bookmark["date_favorited"] is not None:
                            bookmark_dict["date_favorited"] = bookmark["date_favorited"].replace(" ", "T")
                        else:
                            bookmark_dict["date_favorited"] = bookmark["date_favorited"]
                        bookmark_dict["article__title"] = bookmark['article']['title']
                        bookmark_dict["archive"] = bookmark["archive"]
    
                        export_json['bookmarks'].append(bookmark_dict)

                    if 'html' in export_formats:
                        # del.icio.us Bookmarks.html format
                        bookmark_datetime = datetime.strptime(bookmark["date_added"], '%Y-%m-%d %H:%M:%S')
                        bookmark_html_date = int(mktime(bookmark_datetime.timetuple()))
                        bookmark_html_tags = ""
                        i = 0
                        for tag in bookmark['tags']:
                            bookmark_html_tags += tag['text']
                            if i < len(bookmark['tags']) - 1:
                                bookmark_html_tags += ','
                            i += 1
                        bookmark_html = '<DT><A HREF="{url}" ADD_DATE="{date}" PRIVATE="0" TAGS="{tags}">{title}</A>\n'.format(
                            url=bookmark['article']['url'],
                            date=bookmark_html_date,
                            tags=bookmark_html_tags,
                            title=bookmark['article']['title'])
                        if bookmark['article']['dek']:
                            bookmark_html += '<DD>{notes}\n'.format(notes=bookmark['article']['dek'])
                        export_html += bookmark_html

                    bookmark_export_count += 1
                
                # Raw API format
                if 'json' in export_formats:
                    export_jsonraw[tmp_page] = bookmarks_response_dict
                
            else:
                click.echo(click.style("""Sorry! We could not import all your data successfully.
  We have given up and aborted the export and after {threshold} attempts.
  The Readability API produced the error code {status_code}: {reason}
  (Debug details: page {page}, URL {url})""".format(
                    status_code=bookmarks_response.status_code,
                    reason=bookmarks_response.reason,
                    threshold=error_threshold,
                    page=tmp_page,
                    url=bookmarks_response.url), fg='red'))
                error_count += 1
                if error_count > error_threshold:
                    break

            bookmark_pages_export_count += 1
            bar.update(bookmark_pages_export_count)
    
    return {'json': export_json, 'html': export_html, 'jsonraw': export_jsonraw}


def write_export_data(filetype='json', directory=None, filename=None, data=None):
    file_path = path.join(directory, filename)
    with open(file_path, 'a') as export_file:
        if filetype == 'json':
            export_data = json.dumps(data, indent=4)
        else:
            export_data = data
        
        if 'jsonraw' in filename:
            click.echo(" We are are now writing the raw Readability Reader API export data to your hard drive.")
        elif 'json' in filename:
            click.echo(" All your bookmarks have been processed and were converted to JSON.")
        elif 'html' in filename:
            click.echo(" All your bookmarks have been processed and were converted to HTML.")
        else:
            click.echo(" We are are now writing a file with all your links to your hard drive.")
        export_file.write(export_data)
    # implicit close()
        
    return {'file_path': file_path, 'file_size': path.getsize(file_path)}


if __name__ == '__main__':
    readability_exporter()
