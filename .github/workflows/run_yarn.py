from subprocess import check_call

with open('.git/HEAD') as fh:
    branch_name = fh.read().strip()

print(branch_name)
branch_name = branch_name.replace('ref: refs/heads/dependabot/npm_and_yarn/app/', '')
print(branch_name)
if '/' in branch_name:
    branch_name = "@" + branch_name

branch_name = branch_name.rsplit('-', 1)[0]
print(branch_name)

check_call(['yarn', 'up', branch_name], cwd='app')
