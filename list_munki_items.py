#!/usr/local/munki/munki-python

import argparse
import csv
from distutils.version import LooseVersion
from Foundation import CFPreferencesCopyAppValue
import os
import plistlib
import sys
from urllib.parse import urlparse

def get_options():
    parser = argparse.ArgumentParser(description='Lists latest versions of unique items in the Munki repo. By default, fetches only items that are optional installs in any manifests. Will output a .csv to your desktop folder.')
    parser.add_argument('--managedinstalls', help='The list of items will also include managed installs items', action='store_true')
    parser.add_argument('--featuredoptionals', help='The list of items will exclude optional installs that are not featured', action='store_true')
    parser.add_argument('--onlycatalog', help='Include items from only this catalog')
    parser.add_argument('--repofolder', help='Specify a Munki repo folder, instead of having the script try to autodetect the repo based on munkiimport settings. This may be particularly helpful if your repo is a network share mounted via SMB.')
    parser.add_argument('--csvname', help='By default, the output filename will be munki_items_available.csv. Use this flag to specify a different name.')
    args = parser.parse_args()
    if args.managedinstalls:
        managed = True
    else:  
        managed = False
    if args.featuredoptionals:
        featured = True
    else:
        featured = False
    if args.onlycatalog:
        onlycatalog = args.onlycatalog
    else:
        onlycatalog = False
    if args.repofolder:
        repofolder = args.repofolder
    else:
        repofolder = False
    if args.csvname:
        csvname = args.csvname
    else:
        csvname = False
    return managed,featured,onlycatalog,repofolder,csvname

def get_repo():
    try:
        repo_url = CFPreferencesCopyAppValue('repo_url', 'com.googlecode.munki.munkiimport')
    except:
        repo = False
    if not repo_url:
        repo = False
    else:
        url_parts = urlparse(repo_url)
        repo = url_parts.path
    return repo

def versionless_name(item_name):
    '''
    It's possible to add a specific version of an app to a manifest and not just the app name
    Munki considers a hyphen to denote that the version will be afterwards, so there should be no hyphens
    in item names. We just want the highest version number available in the repos - we don't care about a
    specific version for the purposes of this script
    https://github.com/munki/munki/wiki/FAQ#q-i-keep-seeing-warnings-like-warning-could-not-process-item-office2011_update-1442-for-update-no-pkginfo-found-in-catalogs-production-yet-there-is-definitely-an-item-named-office2011_update-1442-in-the-production-catalog-what-is-happening
    '''
    if '-' in item_name:
        name_parts = item_name.split('-')
        cleaned_name = name_parts[0]
    else:
        cleaned_name = item_name
    return cleaned_name

def add_to_list(list_items, plist_contents, current_key):
    if current_key in plist_contents.keys() and isinstance(plist_contents[current_key], list):
        for item in plist_contents[current_key]:
            if item not in list_items.keys():
                list_items[versionless_name(item)] = {}

def get_manifest_usage(repo, managed, featured):
    # Manifests directory
    manifests = os.path.join(repo, 'manifests')
    if not os.path.isdir(manifests):
        print("ERROR: Can't find manifests directory at {}".format(manifests))
        sys.exit(1)
    # Set up dictionary to store items found
    list_items = {}
    # Walk through the manifests directory and subdirectories
    for root, subdirs, files in os.walk(manifests):
        for file in files:
            if file.startswith('.'):
                continue
            full_path = os.path.join(root, file)
            try:
                manifest_file = open(full_path, 'rb')
            except:
                print('WARNING: Unable to open file {}'.format(file))
                continue
            try:
                manifest_contents = plistlib.load(manifest_file)
            except:
                print('WARNING: Unable to read contents from {}'.format(file))
                continue
            manifest_file.close()
            if featured:
                add_to_list(list_items, manifest_contents, 'featured_items')
            else:
                add_to_list(list_items, manifest_contents, 'optional_installs')
            if managed:
                add_to_list(list_items, manifest_contents, 'managed_installs')
    return list_items

def get_items_info(repo, list_items, onlycatalog):
    # pkgsinfo directory
    pkgsinfo = os.path.join(repo, 'pkgsinfo')
    if not os.path.isdir(pkgsinfo):
        print("ERROR: Can't find pkgsinfo directory at {}".format(pkgsinfo))
        sys.exit(1)
    # Walk through the pkgsinfo directory and subdirectories
    for root, subdirs, files in os.walk(pkgsinfo):
        for file in files:
            if file.startswith('.'):
                continue
            full_path = os.path.join(root, file)
            try:
                pkginfo_file = open(full_path, 'rb')
            except:
                print('WARNING: Unable to open file {}'.format(file))
                continue
            try:
                pkginfo_contents = plistlib.load(pkginfo_file)
            except:
                print('WARNING: Unable to read contents from {}'.format(file))
                continue
            pkginfo_file.close()
            # Check that the name key exists in the pkginfo
            if ('name' in pkginfo_contents.keys()
                # And that the name of the pkginfo is in the list of items we care about
                and pkginfo_contents['name'] in list_items.keys()
                # And check that it's either not only to a specific catalog...
                and (not onlycatalog
                    # or that it is a specific catalog and the specific catalog the user asked for
                    or (onlycatalog
                        and 'catalogs' in pkginfo_contents.keys()
                        and isinstance(pkginfo_contents['catalogs'], list)
                        and onlycatalog in pkginfo_contents['catalogs']))
                ):
                # There should be a version for the pkginfo, but we'll just double-check anyway
                if 'version' in pkginfo_contents.keys():
                    # If the version key doesn't already exist in the list_items...
                    if (('version' not in list_items[pkginfo_contents['name']].keys())
                        # Or it does exist and this is now a higher version...
                        or ('version' in list_items[pkginfo_contents['name']].keys()
                            and LooseVersion(list_items[pkginfo_contents['name']]['version']) < LooseVersion(pkginfo_contents['version']))):
                        # Up the version
                        list_items[pkginfo_contents['name']]['version'] = pkginfo_contents['version']
                        # Update the description
                        if 'description' in pkginfo_contents.keys():
                            list_items[pkginfo_contents['name']]['description'] = pkginfo_contents['description']
                        # Update the display name
                        if 'display_name' in pkginfo_contents.keys():
                            list_items[pkginfo_contents['name']]['display_name'] = pkginfo_contents['display_name']
                        # If it's only a specific catalog, add that as well, so we can isolate these... it means we'll have a lot of 
                        # extra stuff in the dictionary, but we don't have to display that all
                        if onlycatalog and 'catalogs' in pkginfo_contents.keys() and onlycatalog in pkginfo_contents['catalogs']:
                            list_items[pkginfo_contents['name']]['catalog'] = True

def write_csv(list_items, csvname, onlycatalog):
    if csvname:
        csv_file = os.path.join(os.path.expanduser('~/Desktop'), csvname)
    else:
        csv_file = os.path.expanduser('~/Desktop/munki_items_available.csv')
    if os.path.exists(csv_file):
        print('ERROR: file {} already exists. Exiting...'.format(csv_file))
        sys.exit(1)
    with open(csv_file, 'w', newline='') as csv_open_file:
        munkilist_writer = csv.writer(csv_open_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        munkilist_writer.writerow(['Name','Description','Version'])
        for item,item_info in list_items.items():
            if not onlycatalog or (onlycatalog and 'catalog' in item_info.keys() and item_info['catalog'] == True):
                print('Writing {} information to CSV'.format(item))
                munkilist_writer.writerow([item_info.get('display_name', ''), item_info.get('description', ''), item_info.get('version', '')])
    csv_open_file.close()
    print('\nCSV available at {}'.format(csv_file))

def main():
    # Get options
    managed,featured,onlycatalog,repofolder,csvname = get_options()

    # Get the URL for the Munki repo
    if repofolder:
        repo = repofolder
    else:
        repo = get_repo()
        if not repo:
            print('ERROR: Unable to obtain repo_url for Munki. Run\n\nmunkiimport --configure\n\nto set the URL')
            sys.exit(1)
    print('\nUsing repo {}\n'.format(repo))

    # Get dictionary of items used in manifests
    list_items = get_manifest_usage(repo, managed, featured)

    # Get version numbers and descriptions
    get_items_info(repo, list_items, onlycatalog)

    # Write the relevant info back to a CSV
    write_csv(list_items, csvname, onlycatalog)

if __name__ == '__main__':
    main()
