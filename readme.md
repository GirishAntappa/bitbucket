docker run -v /path/to/bitbucket/data:/var/atlassian/application-data/bitbucket \
    --name="bitbucket" -d -p your_desired_ip_address:7990:7990 atlassian/bitbucket-server

docker run -v /path/to/bitbucket/data:/var/atlassian/application-data/bitbucket --name="bitbucket" -d -p ipaddress:7990:7990 -e "SERVER_HOST=ipaddress" atlassian/bitbucket

docker run -v /path/to/bitbucket/data:/var/atlassian/application-data/bitbucket --name="bitbucket" -d -p ipaddress:7990:7990 -e "SERVER_HOST=0.0.0.0" atlassian/bitbucket

