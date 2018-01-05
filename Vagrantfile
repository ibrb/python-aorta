# -*- mode: ruby -*-
# vi: set ft=ruby :
system 'mkdir', '-p', 'log'

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  config.ssh.forward_agent = true

  config.vm.define "docker" do |docker|
    docker.vm.network "private_network", ip: "192.168.33.10"
    docker.vm.box = "centos/7"
    docker.vm.provider "virtualbox" do |vb|
      vb.memory = "512"
    end
    docker.vm.provision "shell", inline: <<-SHELL
      yum install -y https://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-redhat96-9.6-3.noarch.rpm
      yum update
      yum install -y postgresql96-server postgresql96-contrib
      yum install -y yum-utils device-mapper-persistent-data lvm2
      yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
      yum install -y docker-ce
      systemctl start docker

      # Initialize the PostgreSQL database
      /usr/pgsql-9.6/bin/postgresql96-setup initdb
      systemctl start postgresql-9.6
      systemctl enable postgresql-9.6
      sudo -u postgres createdb aorta

      # Ensure that firewalld allows AMQP connections to the
      # development machine
      service firewalld start
      firewall-cmd --zone=public --add-port=5672/tcp --permanent
      firewall-cmd --reload

      # Install some applications for command-line debugging.
      yum install -y gcc python-devel
      curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py" && python get-pip.py
      pip install python-qpid-proton
    SHELL
  end

end

