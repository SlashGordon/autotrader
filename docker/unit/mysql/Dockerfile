FROM mariadb:10.4

ADD docker/unit/mysql/mysql.cnf /etc/mysql/conf.d/z99-docker.cnf
RUN chown mysql:mysql /etc/mysql/conf.d/z99-docker.cnf \
&& chmod 0644 /etc/mysql/conf.d/z99-docker.cnf