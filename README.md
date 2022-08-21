# About
Nicko's Backup Manager it's a little python program that automates backups and manages it.
It is very useful when you have a lot of files that you need to backup but you don't have sufficient time or it's so tedius for you.

## How does it works?
You just select what files and directories want to backup and the Backup Manager will copy it when you want.

# How To Use
## Adding a File to the List
To add a file to the list, just use the `add file` command.

## Adding a Directory to the List
To add a directory to the list, you need to use the `add dir` command. Also, you can use the `-c` paremeter to backup the directory in a zip file, following this way: `add dir -c`.

## Deleting Something in the List
To delete something that is in the list, you must use the `del` command, following this syntax: `del [<index>]`.

## Visualizing the List
If you want to see the files and directories in the list, you could use the `show` command. It will show you all the files and dirs in the list and some information about it.

## Creating Backups
When you use the `backup` command, all the files and directories in the list are copied in the path that you specified.