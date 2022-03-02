# Example workflow of using git

To get help, just type "git" in the terminal:

    $ git


Our typical workflow is to "create" a repo on github or gitlab, and then clone it. Find the "ssh" or "https" address on the repo page. For example on our lab's github page there is an
"example_fancy_repo"

    cd ~
    git clone https://github.com/HwangLabNeuroCogDynamics/example_fancy_repo.git

If the folder is a git repo, it should contain a .git hidden folder:

    $ cd example_fancy_repo.git
    $ ls -a
    .  ..  .git
    $ ls .git
    branches  config  description  HEAD  hooks  info  objects  refs

You can also clone exiting repos.

You worked on some science/nature worthy data analyses, now you want to track those code with git.

    echo 'print("running fancy analyses")' > code.py

This code is not committed and tracked yet. You can check it with the command "status"

    $ git status

    # On branch master
    #
    # Initial commit
    #
    # Untracked files:
    #   (use "git add <file>..." to include in what will be committed)
    #
    #	code.py

To add this to the "staging area" for commit:

    git add code.py

You will now see the addition of this file is ready to be committed.

    $ git status
    # On branch master
    #
    # Initial commit
    #
    # Changes to be committed:
    #   (use "git rm --cached <file>..." to unstage)
    #
    #	new file:   code.py

Then commit

    git commit

You would have to enter a comment in the message field to describe the commit. For example "first commit"

Then push so the record is on github

    git push

You would have to enter your id and password for github (or gitlab). <br>
If you go to the github page you should see the new file now tracked.

Let us make changes to the code.

    echo 'print("more changes")' >> code.py

You can check the files that are changed:

    git diff
    git status

Let us commit the changes:

    git add code.py
    git commit
    git push

Check again on github.

What about adding new files?

    echo 'print("more fancy work")' > new_code.py
    git status

Let us add the file to the staging area, then commit and push

    git add new_code.py
    git commit
    git push


If you need to restore a version of a particular file. You can first use git log to check the history of commits:

    $ git log

        commit fd95309aac7f3219b810b7c4bb9152742e0f6d0d
    Author: Kai Hwang <kai.hwang@gmail.com>
    Date:   Tue Jun 30 23:19:18 2020 -0500

        more changes to code.py

    commit da43398e49eaaba406722650d858549ad0880e47
    Author: Kai Hwang <kai.hwang@gmail.com>
    Date:   Tue Jun 30 23:18:22 2020 -0500

        add code.py

If you identified a version that you would like to restore to, you can then use git checkout to restore a particular file:

    git checkout da43398e49eaaba406722650d858549ad0880e47 code.py

If you check the status, you will notice changes are not committed yet.

    $ git status

    # On branch master
    # Your branch is ahead of 'origin/master' by 2 commits.
    #   (use "git push" to publish your local commits)
    #
    # Changes to be committed:
    #   (use "git reset HEAD <file>..." to unstage)
    #
    #	modified:   code.py

So if you want to commit to this previous version of this file. you have to do

    git add code.py
    git commit -m "restore to previous version"
    git push


We can also create "branches" to work on a different version of the code:

    git branch test_new_ideas

You have to use git checkout to switch between branches. Always use git status to check which branch you are on:

    git checkout test_new_ideas
    git status
    git checkout master
    git status

Let us create a new file in the new branch

    git checkout test_new_ideas
    echo 'print("novel task running")' > new_idea.py
    git add new_idea.py
    git commit -m "new file in this branch"

You can compare the branches
    git diff master test_new_ideas
    git diff test_new_ideas

you can "merge" changes in the test_new_ideas branch with the master branch

    git checkout master
    git merge test_new_ideas master

Something I haven't quite figured out is if there are multiple users working on the same branch, how do we merge changes from different users?
