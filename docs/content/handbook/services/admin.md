# Admin portal

`src/app/admin/main.py`: a [Streamlit](https://streamlit.io) app at
<http://localhost:8501>. It shows the API's health and reads straight from Neo4j (edition,
version, node count), which makes it the one frontend allowed past the API.

With mock sign-on, it first asks for an email and password and lets in only members whose role
is `admin` (in the default brand, Ada Lovelace); the sign-in is checked by the API's
`/auth/login`, and the sidebar shows who is signed in with **Sign out**. That gate is a demo,
not security: keep the portal on a private network or behind real authentication in
production; in the production compose overlay its port stays bound to `127.0.0.1`.
