Website to help folks in Indiana find food pantries and their trustee offices in their county or from their address.

WARNING: Data is fetched pretty broadly. There is no expectation for 100% accuracy at this time. 
Indiana township trustee information seems to be pretty decentralized, which makes it difficult to confirm if data is good or not.

To run via docker

```bash
docker build -t indianaresourcemap .
docker run -p 5000:5000 indianaresourcemap
```

To update (yes this should be in docker-compose, and this should be using a database. I'm working on that!)

```bash
docker build -t indianaresourcemap . #build a fresh instance of the image
docker container ls #get the container id of the container
docker container rm -f <container id>
docker run -d -p 5000:5000 indianaresourcemap
```

PRs welcome.
