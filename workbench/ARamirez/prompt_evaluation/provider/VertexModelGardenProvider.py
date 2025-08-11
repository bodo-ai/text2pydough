from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from google.cloud import aiplatform
import asyncio
import logging

logger = logging.getLogger(__name__)


class VertexAIClient(BaseModel):
    """Synchronous Vertex AI prediction client."""
    endpoint: aiplatform.Endpoint
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def predict(self, instances: List[Dict[str, Any]], parameters: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        try:
            return self.endpoint.predict(instances, parameters=parameters, use_dedicated_endpoint=True, **kwargs)
        except Exception as e:
            logger.exception("Vertex AI synchronous prediction failed")
            raise RuntimeError(f"Vertex AI predict() failed: {e}") from e


class VertexAIAsyncClient(BaseModel):
    """Asynchronous Vertex AI prediction client."""
    endpoint: aiplatform.Endpoint
    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def predict(self, instances: List[Dict[str, Any]], **kwargs) -> Any:
        try:
            return await self.endpoint.predict_async(instances, **kwargs)
        except Exception as e:
            logger.exception("Vertex AI asynchronous prediction failed")
            raise RuntimeError(f"Vertex AI predict_async() failed: {e}") from e


class VertexAIModelGarden(BaseModel):
    """Flexible Vertex AI Model Garden wrapper (raw prediction focus)."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        protected_namespaces=(),
    )

    # Core configuration
    project: str = Field(..., description="GCP project ID")
    endpoint_id: str = Field(..., description="Vertex AI endpoint ID or full path")
    location: str = Field(default="us-central1", description="GCP location")

    # Optional: control initialization
    lazy_init: bool = Field(default=True, description="Delay endpoint creation until first use")

    # Internal clients (private attributes, not Pydantic fields)
    _client: Optional[VertexAIClient] = PrivateAttr(default=None)
    _async_client: Optional[VertexAIAsyncClient] = PrivateAttr(default=None)

    def _get_endpoint(self) -> aiplatform.Endpoint:
        """Create or reuse a Vertex AI endpoint instance."""
        logger.debug("Initializing Vertex AI endpoint: %s", self.endpoint_id)
        return aiplatform.Endpoint(
            endpoint_name=self.endpoint_id,
            project=self.project,
            location=self.location
        )

    def _ensure_clients(self) -> None:
        """Lazy-init sync and async clients if needed."""
        if self._client is None:
            endpoint = self._get_endpoint()
            self._client = VertexAIClient(endpoint=endpoint)
            self._async_client = VertexAIAsyncClient(endpoint=endpoint)

    @property
    def endpoint_path(self) -> str:
        """Return the endpoint path."""
        if self._client:
            return self._client.endpoint.name
        return f"projects/{self.project}/locations/{self.location}/endpoints/{self.endpoint_id}"

    def set_endpoint(self, endpoint_id: str, location: Optional[str] = None) -> None:
        """Switch to a different deployed model without reinstantiating the object."""
        logger.info("Switching endpoint from %s to %s", self.endpoint_id, endpoint_id)
        self.endpoint_id = endpoint_id
        if location:
            self.location = location
        self._client = None
        self._async_client = None  # Will re-init on next call

    def predict_raw(self, instances: List[Dict[str, Any]], parameters: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """Run a raw synchronous prediction."""
        self._ensure_clients()
        logger.debug("Sending sync prediction request with %d instances", len(instances))
        return self._client.predict(instances, parameters=parameters, **kwargs)

    async def apredict_raw(self, instances: List[Dict[str, Any]], **kwargs) -> Any:
        """Run a raw asynchronous prediction."""
        self._ensure_clients()
        logger.debug("Sending async prediction request with %d instances", len(instances))
        return await self._async_client.predict(instances, **kwargs)
