import torch

from shared import model

QUERY_PREFIX = "Represent this query for searching relevant code: "


def batch_embed(texts):
    embeddings = []

    for text in texts:
        with torch.no_grad():
            embeddings.append(model.encode(text))
        if torch.backends.mps.is_available() and model.device.type == 'mps':
            torch.mps.empty_cache()
        elif torch.cuda.is_available() and model.device.type == 'cuda':
            torch.cuda.empty_cache()

    if len(embeddings) > 0:
        return embeddings
    else:
        return None


def batch_embed_passage(texts):
    return batch_embed(texts)


def batch_embed_query(texts):
    return batch_embed([f'{QUERY_PREFIX}{text}' for text in texts])
