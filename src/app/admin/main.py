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
