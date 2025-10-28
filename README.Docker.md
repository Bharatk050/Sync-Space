### Building and running your application

Before starting, ensure you have a `.env` file with your Groq API key:
```
GROQ_API_KEY=your_groq_api_key_here
```

When you're ready, start your application by running:
```bash
docker compose up --build
```

Your application consists of two services:
- **Backend API**: Available at http://localhost:8000
- **Frontend UI**: Available at http://localhost:8501 (Streamlit)

### Deploying your application to the cloud

First, build your image, e.g.: `docker build -t myapp .`.
If your cloud uses a different CPU architecture than your development
machine (e.g., you are on a Mac M1 and your cloud provider is amd64),
you'll want to build the image for that platform, e.g.:
`docker build --platform=linux/amd64 -t myapp .`.

Then, push it to your registry, e.g. `docker push myregistry.com/myapp`.

Consult Docker's [getting started](https://docs.docker.com/go/get-started-sharing/)
docs for more detail on building and pushing.

### References
* [Docker's Python guide](https://docs.docker.com/language/python/)