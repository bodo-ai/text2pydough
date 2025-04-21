#!/bin/bash

export AZURE_API_KEY="CLQAXkuwkcBxwpVB0fuL9KmIMGP3GLhTBZcAGezHh6CRZhfqq9fPJQQJ99BBACHYHv6XJ3w3AAAAACOGSJD4"
export AZURE_BASE_URL="https://ai-arnoldo2137ai929428123129.services.ai.azure.com/models"
export GOOGLE_PROJECT_ID="solid-drive-448717-p8"
export GOOGLE_REGION="us-central1"
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/solid-drive-448717-p8-757817f0ec29.json"


CONDA_BASE_PATH=$(conda info --base)

$CONDA_BASE_PATH/envs/aisuite_deepseek/bin/jupyter notebook llm_demo_final_vRK_v2.ipynb \
  --port=8888 \
  --ip=0.0.0.0 \
  --no-browser
