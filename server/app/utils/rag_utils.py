from langchain.text_splitter import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


async def recursive_text_splitter(
    text: str, chunk_size: int = 500, chunk_overlap: int = 50
):
    """
    Splits text into chunks using LangChain's RecursiveCharacterTextSplitter.
    This splitter tries to split on natural language boundaries while maintaining chunk size constraints.

    Args:
        text (str): The input text to be split
        chunk_size (int): The target size of each chunk in characters
        chunk_overlap (int): The number of characters to overlap between chunks

    Returns:
        list[str]: List of text chunks
    """
    if not text:
        return []

    # Initialize the text splitter with sentence-aware separators
    text_splitter = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", "! ", "? ", "… ", "; ", ", ", " ", ""],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )

    # Split the text into chunks
    chunks = text_splitter.split_text(text)
    return chunks


async def markdown_splitter(text, chunk_size: int = 500, overlap_size: int = 50):
    """
    Splits markdown text based on headers first, then applies recursive text splitting on each section.

    Args:
        text (str): The markdown text to be split
        chunk_size (int): The target size of each chunk in characters
        overlap_size (int): The number of characters to overlap between chunks

    Returns:
        list: List of document chunks with metadata about headers
    """
    # First split by markdown headers
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")],
        strip_headers=True,
    )

    md_splits = md_splitter.split_text(text)

    result_chunks = []
    for doc in md_splits:
        content = doc.page_content

        text_chunks = await recursive_text_splitter(content, chunk_size, overlap_size)

        result_chunks.extend(text_chunks)

    return result_chunks
