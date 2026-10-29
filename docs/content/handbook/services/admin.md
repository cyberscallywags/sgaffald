# Admin portal

`src/app/admin/main.py`: a [Streamlit](https://streamlit.io) app at
<http://localhost:8501>. It shows the API's health and reads straight from Neo4j (edition,
version, node count), which makes it the one frontend allowed past the API.

Keep it on a private network or behind authentication in production; in the production
compose overlay its port stays bound to `127.0.0.1`.
