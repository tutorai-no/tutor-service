# Deployment

## Deploying to Digital Ocean

Connect to the server using ssh
```bash
ssh -i "~/.ssh/tutorai" root@46.101.107.247
```

To deploy the changes to the server, you need to pull the changes from the repository and restart the docker containers.
```bash
git pull
docker compose down; docker compose up --build -d
```

## Acquiring a SSH key

To connect to the server, you need to have a SSH key. If you don't have one, you can generate one using the following command.
```bash
ssh-keygen
```

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/tutorai
```
# Deploy 

## Deploying to Digital Ocean

Connect to the server using ssh
```bash
ssh -i "~/.ssh/tutorai" root@46.101.107.247
```

To deploy the changes to the server, you need to pull the changes from the repository and restart the docker containers.
```bash
git pull
docker compose down; docker compose up --build -d
```

## Acquiring a SSH key

To connect to the server, you need to have a SSH key. If you don't have one, you can generate one using the following command.
```bash
ssh-keygen
```

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/tutorai
```