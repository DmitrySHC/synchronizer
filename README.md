## Synchronizer
___

This script allows synchronizing two directories. While the script is running, the directory-replica will be kept up to date. 

As arguments, you must specify:
1) Path to the folder you want to track;
2) Path to the replica folder (will create automatically);
3) Path to the logs (will create automatically);
4) Synchronization interval (in seconds).

For example:
>python sync.py 'C:\path\to\source' 'C:\path\to\target' 'C:\path\to\logs' 10
>
>python sync.py source target logs 10

In unix/linux use:
> python3 sync.py 'C:\path\to\source' 'C:\path\to\target' 'C:\path\to\logs' 10
> 
> python3 sync.py source target logs 10


To interrupt the program execution press "ctrl+с" and wait to current synchronization end.