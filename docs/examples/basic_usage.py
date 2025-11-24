"""Basic usage example for Pylight framework."""

from src.presentation.app import LightApi
from src.domain.entities.rest_endpoint import RestEndpoint
from sqlalchemy import Column, Integer, String


class Product(RestEndpoint):
    """Product model example."""

    __tablename__ = "product"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    price = Column(Integer)


if __name__ == "__main__":
    app = LightApi(
        database_url="sqlite:///example.db",
        swagger_title="Example API",
        swagger_version="1.0.0",
    )

    app.register(Product)
    app.run(host="localhost", port=8000)

