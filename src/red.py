"""Construcción de redes de participación del Laboratorio 6."""
from __future__ import annotations

import networkx as nx
import pandas as pd


def build_bipartita(comments_df: pd.DataFrame) -> nx.Graph:
    """Crea la red no dirigida autor-video con comentarios como peso."""
    columnas = {"author_channel_id", "video_id"}
    faltantes = columnas - set(comments_df.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {sorted(faltantes)}")

    comments = comments_df.dropna(subset=list(columnas)).copy()
    autores = set(comments["author_channel_id"])
    videos = set(comments["video_id"])
    if autores & videos:
        raise ValueError("Los identificadores de autores y videos deben ser disjuntos")

    graph = nx.Graph()
    for author_id, group in comments.groupby("author_channel_id", sort=True):
        graph.add_node(
            author_id,
            bipartite=0,
            tipo="autor",
            author_name=group["author_name"].dropna().iloc[0]
            if "author_name" in group and group["author_name"].notna().any()
            else "",
            author_handle=group["author_handle"].dropna().iloc[0]
            if "author_handle" in group and group["author_handle"].notna().any()
            else "",
            n_comentarios=int(len(group)),
            n_videos=int(group["video_id"].nunique()),
        )

    for video_id, group in comments.groupby("video_id", sort=True):
        graph.add_node(
            video_id,
            bipartite=1,
            tipo="video",
            channel_id=group["channel_id"].dropna().iloc[0]
            if "channel_id" in group and group["channel_id"].notna().any()
            else "",
            channel_name=group["channel_name"].dropna().iloc[0]
            if "channel_name" in group and group["channel_name"].notna().any()
            else "",
            n_comentarios=int(len(group)),
            n_autores=int(group["author_channel_id"].nunique()),
        )

    pesos = comments.groupby(["author_channel_id", "video_id"]).size()
    graph.add_weighted_edges_from(
        (author_id, video_id, int(weight))
        for (author_id, video_id), weight in pesos.items()
    )
    return graph


def proj_autores(bipartita: nx.Graph) -> nx.Graph:
    """Proyecta autores con peso igual al número de videos compartidos."""
    autores = [
        node
        for node, data in bipartita.nodes(data=True)
        if data.get("bipartite") == 0
    ]
    return nx.algorithms.bipartite.weighted_projected_graph(bipartita, autores)


def proj_videos(bipartita: nx.Graph) -> nx.Graph:
    """Proyecta videos con peso igual al número de autores compartidos."""
    videos = [
        node
        for node, data in bipartita.nodes(data=True)
        if data.get("bipartite") == 1
    ]
    return nx.algorithms.bipartite.weighted_projected_graph(bipartita, videos)


def _self_check() -> None:
    import eda

    _, comments = eda.cargar_procesados()
    bipartita = build_bipartita(comments)
    autores = proj_autores(bipartita)
    videos = proj_videos(bipartita)

    assert not bipartita.is_directed()
    assert nx.algorithms.bipartite.is_bipartite(bipartita)
    assert bipartita.number_of_nodes() == 351
    assert bipartita.number_of_edges() == 343
    assert sum(nx.get_edge_attributes(bipartita, "weight").values()) == 406
    assert sum(data["weight"] > 1 for _, _, data in bipartita.edges(data=True)) == 40
    assert autores.number_of_nodes() == 332
    assert videos.number_of_nodes() == 19
    assert videos.number_of_edges() == 11
    print("red.py: self-check OK")
    print(
        f"  bipartita={bipartita.number_of_nodes()} nodos, "
        f"{bipartita.number_of_edges()} aristas; "
        f"proyecciones={autores.number_of_edges()} autor-autor, "
        f"{videos.number_of_edges()} video-video"
    )


if __name__ == "__main__":
    _self_check()
