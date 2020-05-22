# MunkiItemsList
Lists latest version of Munki items available in manifests

## What's the point of this project?
Honestly, I created this just for fun. I don't need this, but I've seen people sometimes asking about how to list out software to advertise (in a PDF, on a website, etc.) is available in the Munki repo, so maybe someone will find this useful.

## How to run the script
You can just run the script as is, and it will try to pull the `repo_url` information based on what's in your `com.googlecode.munki.munkiimport` preferences. Right now, it's not actually trying to mount any network shares the way `munkiimport` does, but there's an option to specify a different folder, in case you want to mount the share yourself.

The script will then generate on your desktop a comma-separated values file called `munki_items_available.csv`, though you have the option to specify a different filename.

First, it combs through the manifests to find optional installs items, and then it tries to find the latest versions available of each of those items.

## Optional options

### Include Managed Installs
By default, only optional installs are considered. If you want to also include managed installs, add the `--managedinstalls` flag.

Example: `./list_munki_items.py --managedinstalls`

### Only Featured Optional Installs
If you want to look at featured items instead of all optional installs, add the `--featuredoptionals` flag. The script does not check to see if featured items are also in the optional installs, but if you have featured items that are not optional installs, Munki itself (when run on the client machine) will give a warning that an item is in featured install but not optional installs.

Example: `./list_munki_items.py --featuredoptionals`

### Only a specified catalog
If you want to list the highest version available, and you don't want to tell your users version X+1 is available when that's still in testing, and version X is what's really in production, you can use the `--onlycatalog` flag.

Example: `./list_munki_items.py --onlycatalog production`

That would select only items that have the `production` catalog enabled.

### Custom Munki folder
This script isn't super sophisticated, so it isn't going to try to mount a network share if that's what your `repo_url` is in your `munkiimport` settings. If you have a `repo_url` like `file:///Users/Shared/munki_repo`, that's fine, and this script should work fine with that. If, however, you have a `repo_url` like `smb://yourwebserver.com/munki_repo`, you may have to manually mount the share, and then run the script like this:
`./list_munki_items.py --repofolder /Volumes/munki_repo`

### Custom .csv filename
By default, the script will output to your desktop a .csv called `munki_items_available.csv`, but if you prefer a different filename, you can add a flag to specify your own preferred filename:
`./list_munki_items.py --csvname awesomemunkiitems.csv`

### Multiple flags
You can combine flags. For example, if you wanted to get optional installs and managed installs that are in only the `testing` catalog, you'd run
`./list_munki_items.py --managedinstalls --onlycatalog testing`

Or if you wanted to get only featured optional installs (not all optional installs) and also all the managed installs, you'd run
`./list_munki_items.py --managedinstalls --featuredoptionals`
