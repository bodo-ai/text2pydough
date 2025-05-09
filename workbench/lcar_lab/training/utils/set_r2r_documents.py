from r2r import R2RClient
# pip install 'r2r[core]'

client = R2RClient("http://localhost:7272")

file_path = '../training_data/rag_data/repomix-output-PyDough-5ff410e3bbe246a24b52fd56934c7b6c23da3fb0.md'

ingest_response = client.documents.create(
      file_path=file_path,
      ingestion_mode="fast"
)

#delete_response = client.documents.delete("6b2793be-adcb-5fa2-91e6-fd91b331d695")

print(ingest_response)