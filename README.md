# About
Nicko's Backup Manager it's a little python program that automates backups and manages it.
It is very useful when you have a lot of files that you need to backup but you don't have sufficient time or it's so tedius for you.  
**This project is under the GNU GPL-3.0 license**

# How To Use
## Select a List
First, you must select a list. For default, there is one list in the program, but you can create or import more.
To select a list, use the `list select [<index>]` command. For example, to select the first one you must use the `list select 0` command.

## Add a File to a List
To add a file to a list, use the `add file` command.

## Add a Directory to a List
To add a directory to a list, you need to use the `add dir` command. Also, you can use the `-c` (same as `--commpress`) option to backup the directory in a zip file, following this way: `add dir -c`.

## Deleting Something in a List
To delete something that is in a list, you must use the `del` command, following this syntax: `del [<index>]`.

## Visualizing the List
If you want to see the files and directories in the list, you could use the `show` command. It will show you all the files and dirs in the list and some information about it.

## Creating Backups
When you use the `backup` command, all the files and directories in the list are copied in the path that you specified.

## Restoring Data
You could use the `restore` command to restore all the data in a list.

# About Lists
You can write down what files and dirs you want to backup or restore using a list. It is very useful is you have a lot of different files and dirs (also called **resource(s)**) and you want to order them by classification.

## Create a List
To create a new list, you must use the `list create` command. When you use it, you must input a name to your list. After that, you have your list created.

## View all the Lists
If you wanna know what lists you have loaded in the software, you can use the `list show` command.  
Also, you can add an index next to the command. It will show you the content of the list at the index you indicated.

## Select a List
To backup or restore the files in a list, or add or remove the written down resources in it, you must select it first.  
To do that, you have to use the `list select [<index>]` command. If you don't know the index of the list that you wanna select, use the `list show` command and pay attention to the number at the left of the list's name.  
```
[1] - <list name> | X elements
^^^
List's index.
```

## Remove a List
To remove a list, you must use the `list remove [<index>]` command.

## Rename a List
If you don't like the name of a list or you just wanna change it, use the `list rename [<index>]` command.

## Export a List
To export a list to a file, just use the `list export [<index>]` command. A window will be opened for you to indicate where you want to save the file and then you will have your very beautiful list in JSON format.

## Import a List
If you have an exported list and you wanna import it, you must use the `list import` command. A window will be opened for you to indicate what file contains the list and then you will have to confirm if is the correct list or not. If you want to skip this final step, just use the `-d` option (same as `--direct`).