
# Deployment Guide
Welcome to the complete guide for deploying any app using the FastAPI backend template! This step-by-step documentation will walk you through setting up your server, adding a basic firewall, and securing your app with a Let’s Encrypt auto-generated certificate. Perfect for beginners, this guide offers a quick, cost-efficient way to self-host your application on a VPS and test your ideas in production. 🚀

**DISCLAIMER:** This guide provides general steps and advice. Be sure to adapt them to fit your application’s needs and project requirements.
## Setup a Linux server

### Create your server

Go to your favorite host service provider ([Ionos](https://ionos.fr), [Infomaniak](https://infomaniak.com), [Digital Ocean Droplets](https://www.digitalocean.com/products/droplets), etc...) and create a non managed server (Cloud, dedicated or VPS).

### Connect to your server
Configure your SSH key (public RSA key under ~/.ssh/id_rsa.pub) or save the root access credential for the first connection, then connect to the server as a root user user:
```
ssh root@<server_ip_address>
```
You probably will have to add this new server to the list of known hosts. Just type 'yes' when the command line ask you about this.

>[!TIP]
This step can differ depending on your provider. For example with Digital Ocean you will not have to set up your SSH connection as it will be already configured for you directly on Digital Ocean dashboard.

### Update your server

Update and upgrade the software on the system:

````
apt update && apt upgrade
````

Optionally you can clean up all residual files related to your system upgrade:
````
apt autoremove -y && apt clean
````

### Set the hostname

Change the hostname of the server to reflect the use of your brand new server
````
hostnamectl set-hostname <new-server-name>
````

Now set up the hostname in the host file using your favorite text editor (I'm gonna go with nano to keep it simple)
````
nano /etc/hosts
````
In the open file just under the localhost line add your <server_ip_address> then hit the "Tab" key and add your <new-server-name. It should look something like this:

````
127.0.0.1               localhost
<server_ip_address>     <new-server-name>

...
````

### Add a limited user

To avoid using the root user that has unlimited privileges we will have to create a limited user to use as the main account.

````
adduser <username>
````

Now we want to add the user to the sudo group so he can run the admin commands

````
adduser <username> sudo
````

Now that this is done you can log out of the server using "exit" and login with the limited user. 

````
ssh <username>@<server_ip_address>
````
### Setup SSH key authentification

Login as your limited user:

````
su - <username>
````

Make a .ssh/ folder and create the authorized_keys file on the server in the user's home directory.
````
mkdir .ssh
touch ~/.ssh/authorized_keys
````
Now let's go back to your local machine. If you don't have generated an ssh key yet you can run and follow the instructions.
````
ssh-keygen -t ed25519 -C "your_email@example.com"
````
Let's secure copy the ssh key on to the server
````
scp ~/.ssh/id_rsa.pub <username>@<server_ip_address>:~/.ssh/authorized_keys
````
Update the permissions of the .ssh directory

````
sudo chmod 700 ~/.ssh/
sudo chmod 600 ~/.ssh/*
````

Now the ssh connection is setup and you should be able to connect to your user on the server without any password.

Make sure that the ssh connection is working before proceeding to next step otherwise you risk to lose access to your server.

We will now deactivate the password authentication to the server
````
sudo nano /etc/ssh/sshd_config
````
And will want to deactivate to set the variables "PermitRootLogin" and "PasswordAuthentication" to "no" in this config file. To make the changes effective restart the SSH servers
````
sudo systemctl restart sshd
````
or 
````
sudo systemctl restart ssh
````

### \[Optional\] Passwordless login

>[!CAUTION]
>For obvious security reasons passwordless login is not recommended in a Production environment

To make your life easier you may want to navigate across your server without the need of a password. You are already identified by your SSH key so it should be sufficient for non-critical server like a staging server.
To do so you can run the following command:
```
sudo passwd -d <your_user>
```

### \[Recommanded\] Passwordless sudo actions
If you use a server manager service or a Paas like coolify you can also setup a limited user but make sure to allow your user to run all sudo actions without a password like follows:
You need to add the following lines **at the end** of the /etc/sudoers file:
```
<username> ALL=(ALL) NOPASSWD: ALL
```
Use this command to edit your file:
````
sudo visudo -f /etc/sudoers
````

Ready more on [Coolify documentation](https://coolify.io/docs/knowledge-base/server/non-root-user)

### Set up a firewall
Install uncomplicated firewall or 'ufw'
````
sudo apt install ufw
````

Set up the rules (depending on your need but this should cover most of normal usages)
````
sudo ufw default allow outgoing
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
````
Apply the rules
````
sudo ufw enable
````
Verify if everything is setup the way you want
````
sudo ufw status
````
>[!CAUTION]
> **Don’t Lock Yourself Out!**
> If you disable access through port `22` - SSH (or any post you set up to use for your SSH connection), you risk locking yourself out of the server, especially if password login is disabled. Double-check that SSH is allowed (`sudo ufw allow ssh`) before enabling the firewall. If you lose access, recovery may require physical or alternative remote access to the server. Proceed with caution!

# Add your project
Create your target folder, for example:
````
sudo mkdir /var/www
cd /var/www
````

To clone your project, you can use https, in this case you will need a password but in general you will want to setup an ssh connection with your server. To do so you will have to go to the home of your user and create an ssh key. Then add the ssh key of your limited user to your GH account. Depending on your security requirements you may want to consider other approaches with limited access keys for example.


# Deploy your stack
>[!NOTE]
>This is an example of how to quickly deploy your project. Keep in mind to challenge this configuration bases on your project scale and requirements.

Set the hostname of your server
````
export USE_HOSTNAME=<yourdomain.com>
echo $USE_HOSTNAME > /etc/hostname
hostname -F /etc/hostname
````

Download and install docker
````
curl -fsSL get.docker.com -o get-docker.sh
CHANNEL=stable sh get-docker.sh
rm get-docker.sh
````

Download and install docker-compose
>[!TIP]
This download channel should be up to date with the latest version of docker compose. Please refer to the official docker compose documentation in case you encounter any issue during this step.
````
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
source ~/.profile
docker compose version
````

Init the docker swarm
````
docker swarm init
docker node ls
````

>[!TIP]
Depending on your server configuration you may need to assign the ip address manual using this command instead. For example the `--advertise-addr` is necessary in when using a **Digital Ocean Droplet**.
````
docker swarm init --advertise-addr <YOUR_IP_ADDRESS>
````

Create a directory to store Let’s Encrypt certificates:
````
mkdir ./letsencrypt
chmod 600 ./letsencrypt
````

Export the env vars of the project:
````
export TAG=stag
export DOMAIN=yourdomain.com
export STACK_NAME=your-stack-name
````

>[!IMPORTANT]
Don't forget to add your project .env file. You will have to do this manually or via scp since the .env is not in the base repo


>[!TIP]
Depending on your project requirements you may want to avoid setting secret data using .env or variable export. A more production ready solution would be to use a secret manager like Amazon Secrets Manager or Github Secrets.

Finally you can deploy your stack in one line:
````
bash scripts/deploy.sh
````


# Update your stack
Get the latest version of you repo
````
sudo git pull
````

Set the env vars:
````
export TAG=stag
export DOMAIN=yourdomain.com
export STACK_NAME=your-stack-name
````
Rebuild and deploy your project using the deploy.sh script. To make sure your changes are propagated to your website make sure to restart your backend container.
````
bash scripts/deploy.sh

docker service update --force "${STACK_NAME}_backend" -d
````

You can now check the logs of your app and grab a coffee ☕️ while watching request popping in:
````
docker ps
docker service logs -f "${STACK_NAME}_backend"
````

# How to completely delete my stack?
````
docker stack rm "${STACK_NAME}"
docker swarm leave --force
````

Remove containers and images of your project
````
docker rm -f $(docker ps -a -q)
docker volume rm $(docker volume ls -q)
````

Optionally you can also remove all the unused docker data with, this will not affect any running containers:
````
docker system prune
````

If you want to also remove all the unused volumes you can use:
````
docker system prune --volumes
````