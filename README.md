Website to help folks in Indiana find food pantries and their trustee offices in their county or from their address.

WARNING: Data is fetched pretty broadly. There is no expectation for 100% accuracy at this time. 
Indiana township trustee information seems to be pretty decentralized, which makes it difficult to confirm if data is good or not.

## Quick Start with Docker Compose

### First time setup:
```bash
docker-compose up -d
```

### To update the application:
```bash
# Pull latest code changes
git pull

# Rebuild and restart (only rebuilds if code changed)
docker-compose up -d --build
```

### Other useful commands:
```bash
# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Force rebuild (if needed)
docker-compose build --no-cache
docker-compose up -d
```

## Legacy Docker Commands (if not using docker-compose)

```bash
# Build and run
docker build -t indianaresourcemap .
docker run -p 5000:5000 indianaresourcemap

# Update manually
docker build -t indianaresourcemap .
docker container ls
docker container rm -f <container id>
docker run -d -p 5000:5000 indianaresourcemap
```

PRs welcome.
