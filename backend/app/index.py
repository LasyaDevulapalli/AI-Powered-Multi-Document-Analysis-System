import argparse
import sys
from pathlib import Path

# Add parent directory to sys.path so app modules import cleanly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.rag.pipeline import RAGPipeline
from app.core.logging_config import logger

def main():
    parser = argparse.ArgumentParser(description="Multi-Document Knowledge Base Indexing CLI")
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Refuse a destructive re-index. Back up the vector store and "
            "target a separately named collection before rebuilding."
        )
    )
    args = parser.parse_args()

    logger.info("Initializing RAG Pipeline for document collection indexing...")
    pipeline = RAGPipeline()
    
    result = pipeline.index_documents(force_reindex=args.force)

    print("\n==================================================")
    print("           INDEXING EXECUTION SUMMARY             ")
    print("==================================================")
    print(f"Status:             {result['status'].upper()}")
    print(f"Message:            {result['message']}")
    print(f"Total Documents:    {result['total_documents']}")
    print(f"Valid Processed:    {result['valid_documents']}")
    print(f"Failed Documents:   {result['failed_documents']}")
    print(f"PDFs Discovered:    {result.get('pdfs_discovered', result['total_documents'])}")
    print(f"PDFs Extracted:     {result.get('pdfs_extracted', result['valid_documents'])}")
    print(f"PDFs Skipped:       {result.get('pdfs_skipped', result['failed_documents'])}")
    print(f"Chunks Generated:   {result.get('chunks_generated', result['total_chunks'])}")
    print(f"Chunks Indexed:     {result['total_chunks']}")
    print(f"Subjects Indexed:   {', '.join(result.get('subjects_represented', [])) or 'none'}")
    print(f"Extraction Errors:  {result.get('errors', 0)}")
    print(f"Elapsed Time:       {result['elapsed_time']} seconds")
    print("--------------------------------------------------")

    if result.get("details"):
        print("DOCUMENT DETAILS:")
        for doc in result["details"]:
            status_symbol = "OK" if doc["status"] == "success" else "FAIL"
            print(f"  [{status_symbol}] {doc['document_name']} -- {doc['pages']} pages, {doc['chunks']} chunks")
            if doc["error"]:
                print(f"      Error: {doc['error']}")
    print("==================================================\n")

if __name__ == "__main__":
    main()
