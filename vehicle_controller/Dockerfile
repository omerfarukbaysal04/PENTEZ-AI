FROM python:3.9-slim

RUN apt-get update && apt-get install -y openssh-server && mkdir -p /var/run/sshd && echo 'root:1234' | chpasswd && sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY control.py .
COPY start.sh .
RUN chmod +x start.sh

EXPOSE 22
EXPOSE 444

CMD ["./start.sh"]