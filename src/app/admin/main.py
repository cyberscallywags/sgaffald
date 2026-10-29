"""Streamlit admin portal: API health plus direct (admin) access to Neo4j."""

import asyncio

import httpx
import streamlit as st

from app.config import get_settings
from app.db import make_driver
from app.meta import get_meta

settings = get_settings()
title = f"{get_meta().name} admin"
st.set_page_config(page_title=title, layout="wide")
st.title(title)
st.caption(f"Environment: **{settings.app_env}**")


async def graph_stats() -> dict:
    driver = make_driver(settings)
    try:
        records, _, _ = await driver.execute_query(
            "CALL dbms.components() YIELD name, versions, edition "
            "RETURN name, versions[0] AS version, edition",
            database_=settings.neo4j_database,
        )
        counts, _, _ = await driver.execute_query(
            "MATCH (n) RETURN count(n) AS nodes", database_=settings.neo4j_database
        )
        return {**records[0].data(), "nodes": counts[0]["nodes"]}
    finally:
        await driver.close()


def admin_gate() -> None:
    """Mock sign-on: only `admin` members see the portal. It reads Neo4j directly, so keep it
    on a private network as well; this gate is a demo, not security (see the handbook)."""
    if (settings.auth_mode or get_meta().auth.mode) != "mock":
        return
    if member := st.session_state.get("member"):
        st.sidebar.write(f"Signed in as **{member['name']}** ({member['role']})")
        if st.sidebar.button("Sign out"):
            del st.session_state["member"]
            st.rerun()
        return
    with st.form("sign-in"):
        st.subheader("Sign in")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
    if submitted:
        try:
            r = httpx.post(
                f"{settings.api_url}/auth/login",
                json={"email": email, "password": password},
                timeout=5,
            )
        except httpx.HTTPError as exc:
            st.error(f"API unreachable, so nobody can sign in: {exc}")
            st.stop()
        if r.status_code != 200:
            st.error("Wrong email or password")
        elif r.json()["member"]["role"] != "admin":
            st.error("The admin portal is for admin members only")
        else:
            st.session_state["member"] = r.json()["member"]
            st.rerun()
    st.stop()


admin_gate()

col1, col2 = st.columns(2)

with col1:
    st.subheader("API")
    try:
        health = httpx.get(f"{settings.api_url}/health", timeout=5).json()
        st.json(health)
    except httpx.HTTPError as exc:
        st.error(f"API unreachable: {exc}")

with col2:
    st.subheader("Neo4j")
    try:
        st.json(asyncio.run(graph_stats()))
    except Exception as exc:  # admin page should never crash
        st.error(f"Neo4j unreachable: {exc}")

st.subheader("Items")
try:
    st.dataframe(httpx.get(f"{settings.api_url}/items", timeout=5).json(), width="stretch")
except httpx.HTTPError as exc:
    st.error(str(exc))
