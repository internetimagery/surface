""" Git functionality for simple helpful macros """


#  .--.      .--.    ,-----.    .-------.    .--.   .--.          .-./`) ,---.   .--.        .-------. .-------.        ,-----.      .-_'''-.   .-------.        .-''-.     .-'''-.    .-'''-.
#  |  |_     |  |  .'  .-,  '.  |  _ _   \   |  | _/  /           \ .-.')|    \  |  |        \  _(`)_ \|  _ _   \     .'  .-,  '.   '_( )_   \  |  _ _   \     .'_ _   \   / _     \  / _     \
#  | _( )_   |  | / ,-.|  \ _ \ | ( ' )  |   | (`' ) /            / `-' \|  ,  \ |  |        | (_ o._)|| ( ' )  |    / ,-.|  \ _ \ |(_ o _)|  ' | ( ' )  |    / ( ` )   ' (`' )/`--' (`' )/`--'
#  |(_ o _)  |  |;  \  '_ /  | :|(_ o _) /   |(_ ()_)              `-'`"`|  |\_ \|  |        |  (_,_) /|(_ o _) /   ;  \  '_ /  | :. (_,_)/___| |(_ o _) /   . (_ o _)  |(_ o _).   (_ o _).
#  | (_,_) \ |  ||  _`,/ \ _/  || (_,_).' __ | (_,_)   __          .---. |  _( )_\  |        |   '-.-' | (_,_).' __ |  _`,/ \ _/  ||  |  .-----.| (_,_).' __ |  (_,_)___| (_,_). '.  (_,_). '.
#  |  |/    \|  |: (  '\_/ \   ;|  |\ \  |  ||  |\ \  |  |         |   | | (_ o _)  |        |   |     |  |\ \  |  |: (  '\_/ \   ;'  \  '-   .'|  |\ \  |  |'  \   .---..---.  \  :.---.  \  :
#  |  '  /\  `  | \ `"/  \  ) / |  | \ `'   /|  | \ `'   /         |   | |  (_,_)\  |        |   |     |  | \ `'   / \ `"/  \  ) /  \  `-'`   | |  | \ `'   / \  `-'    /\    `-'  |\    `-'  |
#  |    /  \    |  '. \_/``".'  |  |  \    / |  |  \    /          |   | |  |    |  |        /   )     |  |  \    /   '. \_/``".'    \        / |  |  \    /   \       /  \       /  \       /
#  `---'    `---`    '-----'    ''-'   `'-'  `--'   `'-'           '---' '--'    '--'        `---'     ''-'   `'-'      '-----'       `'-...-'  ''-'   `'-'     `'-..-'    `-...-'    `-...-'
#

import subprocess

if False:
    from typing import Optional

# Goal:
#     Add convenience wrapper in the cli to diff two git branches
#     Will need to first check if actually in a git repo
#     Then get the current branch, so we can return
#     Then check there is nothing unstaged, else branch changing may break
#     Export current API to tempfile
#     Then try finally, switch branch and export other API
#     switching back in the finally block


def get_root():  # type: () -> Optional[str]
    """ Get root from current directory """
    # git rev-parse --show-toplevel
    pass


def unstaged_changes():  # type: () -> bool
    """ Check for unstaged changes """
    # git status --porcelain
    pass


def get_branch():  # type: () -> str
    """ Get current branch """
    # git rev-parse --abbrev-ref HEAD
    pass


def set_branch(name):  # type: (str) -> None
    """ Set branch to named """
    # git checkout name
    pass
