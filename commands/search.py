from embed import batch_embed_query
from shared import collection

INNER_RESULTS = 50
OUTER_RESULTS = 3


class Answer:
    def __init__(self, file, score, start, end, document):
        self.file = file
        self.score = score
        self.start = start
        self.end = end
        self.document = document

    def sortByScore(answer):
        return answer.score


def define_search(subparsers):
    search_parser = subparsers.add_parser(
        "search",
        help="Search indexed content"
    )

    search_parser.add_argument(
        "query",
        nargs="+",
        help="Search query"
    )


def handle_search(args):
    query = " ".join(args.query)
    query_tensors = batch_embed_query([query])
    results = collection.query(
        query_embeddings=query_tensors,
        include=["metadatas", "distances", "documents"],
        n_results=INNER_RESULTS
    )

    files = {}

    for i, metadata in enumerate(results["metadatas"][0]):
        file = metadata["file"]

        if file not in files:
            files[file] = []

        files[file].append(i)

    answers = []

    for file in files:
        for i in files[file]:
            a_score = 1 - results["distances"][0][i]
            a_metadata = results["metadatas"][0][i]
            a_start = a_metadata["start"]
            a_end = a_metadata["end"]
            a_document = results["documents"][0][i]

            answer = Answer(file, a_score, a_start, a_end, a_document)

            for j in files[file]:
                if j == i:
                    continue

                b_score = 1 - results["distances"][0][j]
                b_metadata = results["metadatas"][0][j]
                b_start = b_metadata["start"]
                b_end = b_metadata["end"]

                overlap_start = max(a_start, b_start)
                overlap_end = min(a_end, b_end)
                overlap_amount = max(0, overlap_end - overlap_start)

                b_length = b_end - b_start
                overlap = (overlap_amount / b_length) if b_length > 0 else 0

                answer.score += overlap * b_score

            answers.append(answer)

    answers.sort(
        reverse=True,
        key=Answer.sortByScore
    )

    for answer in answers[:OUTER_RESULTS]:
        print(
            f"{answer.file}:{answer.start}:{answer.end}\n{answer.document}\n\n"
        )
