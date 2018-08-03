
import base64

import requests
from flask import Flask, render_template, redirect, request, url_for, abort
from flask_bootstrap import Bootstrap
import random
from urlparse import parse_qs


app = Flask(__name__)
bootstrap = Bootstrap(app)


authorization_base_url = 'https://github.com/login/oauth/authorize'
token_url = 'https://github.com/login/oauth/access_token'
request_url = 'https://api.github.com'
client_id = '5bfc1e5fa3e5e7d25af2'
client_secret = '45cdfa300a39c7a646fbb1a0b415088ccf3f893e'
state = str(random.randrange(100))
access_token = ''

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():

    return redirect(authorization_base_url+'?client_id=' + client_id + '&scope=user%20repo%20public_repo' + \
         '&allow_signup=true' + '&state=' + state)


@app.route('/github_login/github/authorized')
def authorized():

    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': str(request.args.get('code')),
        'state': state
    }
    response = requests.post(token_url, data=data)
    access_token = parse_qs(response.content).get('access_token')[0]
    userdetails = requests.get("https://api.github.com/user?access_token="+access_token).json()
    return render_template('userdetails.html',userdetails=userdetails, access_token=access_token)

@app.route('/repos/<access_token>')
def repos(access_token):
    user = requests.get(request_url+'/user'+'?access_token='+access_token).json()['login']
    response = requests.get(request_url+'/users/' + user + '/repos'+'?access_token='+access_token).json()
    repos = []
    for repo in response:
        repos.append(
            {
                'name': repo['name'],
                'private': repo['private']
            }
        )
    return render_template('list_repo.html', username=user, repos=repos, access_token=access_token)


@app.route('/branches/<username>/<repo>/<access_token>')
def branches(username, repo, access_token):
    response = requests.get(request_url+'/repos/' + username + '/' + repo + '/branches'+'?access_token='+access_token).json()
    branchs = []
    for branch in response:
        branchs.append(
            {
                'name': branch['name'],
                'sha' : branch['commit']['sha']
            }
        )

    return render_template('list_branches.html', user=username, repo=repo, branches=branchs, access_token=access_token)


@app.route('/branches/<username>/<repo>/<branch>/<sha>/<access_token>')
def files(username, repo, branch, sha, access_token):
    response = requests.get(request_url+'/repos/' + username + '/' + repo + '/git/trees/' + sha + '?recursive=1'+'?access_token='+access_token).json()
    files = []
    for tree in response['tree']:
        if tree['type'] != 'tree':
            files.append(
                {
                    'url': tree['url'],
                    'path': tree['path']
                }
            )

    return render_template('list_files.html', user=username, repo=repo, branch=branch, sha=sha, files=files, access_token=access_token)

@app.route('/filecontent', methods=['POST'])
def filecontent():
    response = requests.get(request.form.get('url')+'?access_token='+request.form.get('access_token')).json()
    content = (base64.b64decode(response['content'])).split('\n')
    if request.form.get('path').endswith('.png'):
        return render_template('filecontent.html', content=response['content'])
    else:
        return render_template('filecontent.html', content=content)


if __name__ == '__main__':
    app.run(debug=True)
