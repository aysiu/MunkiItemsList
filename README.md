# MunkiItemsList
Lists latest version of Munki items available in manifests

## What's the point of this project?
Honestly, I created this just for fun. I don't need this, but I've seen people sometimes asking about how to list out software to advertise (in a PDF, on a website, etc.) is available in the Munki repo, so maybe someone will find this useful.

## How to run the script
You can just run the script as is, and it will try to pull the `repo_url` information based on what's in your `com.googlecode.munki.munkiimport` preferences. Right now, it's not actually trying to mount any SMB shares the way `munkiimport` does, but maybe that could be in a future version (pull requests are welcome!).

The script will then generate on your desktop a comma-separated values file called `munki_items_available.csv`.

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

### Multiple flags
You can combine flags. For example, if you wanted to get optional installs and managed installs that are in only the `testing` catalog, you'd run
`./list_munki_items.py --managedinstalls --onlycatalog testing`

Or if you wanted to get only featured optional installs (not all optional installs) and also all the managed installs, you'd run
`./list_munki_items.py --managedinstalls --featuredoptionals`
